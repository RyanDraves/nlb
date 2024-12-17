#include "emb/network/transport/nus_gatt_generated/nus.h"
#include "emb/network/transport/transport.hpp"

#include <functional>

#include "ble/gatt-service/nordic_spp_service_server.h"
#include "btstack.h"
// #include "emb/util/log.hpp"
#include "pico/btstack_cyw43.h"
#include "pico/cyw43_arch.h"
#include "pico/sem.h"

namespace emb {
namespace network {
namespace transport {

namespace {
static constexpr uint16_t kHeartbeatPeriodMs = 1000;

static constexpr uint8_t adv_data[] = {
    // Flags general discoverable, BR/EDR not supported
    0x02,
    BLUETOOTH_DATA_TYPE_FLAGS,
    0x06,
    // Name
    0x06,
    BLUETOOTH_DATA_TYPE_COMPLETE_LOCAL_NAME,
    'P',
    'i',
    'c',
    'o',
    'W',
    0x11,
    BLUETOOTH_DATA_TYPE_COMPLETE_LIST_OF_128_BIT_SERVICE_CLASS_UUIDS,
    0x9e,
    0xca,
    0xdc,
    0x24,
    0xe,
    0xe5,
    0xa9,
    0xe0,
    0x93,
    0xf3,
    0xa3,
    0xb5,
    0x1,
    0x0,
    0x40,
    0x6e,
};
static constexpr uint8_t adv_data_len = sizeof(adv_data);

static void hci_event_callback(uint8_t packet_type, uint16_t channel,
                               uint8_t *packet, uint16_t size);
static void heartbeat_callback(struct btstack_timer_source *ts);
static void packet_callback(uint8_t packet_type, uint16_t channel,
                            uint8_t *packet, uint16_t size);
static void nordic_can_send(void *context);

struct BleImpl {
    int le_notification_enabled;
    uint8_t connect_flag;
    int led_on = true;

    btstack_timer_source_t heartbeat;
    hci_con_handle_t con_handle;
    btstack_context_callback_registration_t send_request;
    btstack_packet_callback_registration_t hci_event_callback_registration;
    std::span<uint8_t> rx_buffer;
    uint16_t rx_size;
    std::span<uint8_t> tx_buffer;

    semaphore_t rx_sem;

    void initialize() {
        sem_init(&rx_sem, 0 /* initial_permits */, 1 /* max_permits */);
    }

    void send(const std::span<uint8_t> &data) {
        if (con_handle != HCI_CON_HANDLE_INVALID) {
            tx_buffer = data;
            send_request.callback = &nordic_can_send;
            nordic_spp_service_server_request_can_send_now(&send_request,
                                                           con_handle);
        }
    }

    std::span<uint8_t> receive(std::span<uint8_t> buffer) {
        rx_buffer = buffer;
        // Wait for the semaphore to be released
        sem_acquire_blocking(&rx_sem);

        // Return the received data
        return rx_buffer.subspan(0, rx_size);
    }

    void stack_event_packet_handler(uint8_t packet_type, uint16_t channel,
                                    uint8_t *packet, uint16_t size) {
        UNUSED(size);
        UNUSED(channel);
        bd_addr_t local_addr;
        if (packet_type != HCI_EVENT_PACKET)
            return;

        uint8_t event_type = hci_event_packet_get_type(packet);
        switch (event_type) {
        case BTSTACK_EVENT_STATE:
            if (btstack_event_state_get_state(packet) != HCI_STATE_WORKING)
                return;
            gap_local_bd_addr(local_addr);
            // LOG << "BTstack up and running on " << bd_addr_to_str(local_addr)
            //     << LOG_END;
            break;
        case HCI_EVENT_CONNECTION_COMPLETE:
            // LOG << "Connected" << LOG_END;
            break;
        case HCI_EVENT_DISCONNECTION_COMPLETE:
            le_notification_enabled = 0;
            // LOG << "Disconnected" << LOG_END;
            connect_flag = 0;
            break;
        default:
            break;
        }
    }

    void can_send_handler() {
        nordic_spp_service_server_send(con_handle, tx_buffer.data(),
                                       tx_buffer.size());
    }

    void packet_handler(uint8_t packet_type, uint16_t channel, uint8_t *packet,
                        uint16_t size) {
        UNUSED(channel);
        switch (packet_type) {
        case HCI_EVENT_PACKET:
            if (hci_event_packet_get_type(packet) != HCI_EVENT_GATTSERVICE_META)
                break;

            switch (hci_event_gattservice_meta_get_subevent_code(packet)) {
            case GATTSERVICE_SUBEVENT_SPP_SERVICE_CONNECTED:
                con_handle =
                    gattservice_subevent_spp_service_connected_get_con_handle(
                        packet);
                // LOG << "Connected with handle " << con_handle << LOG_END;
                connect_flag = 1;
                break;
            case GATTSERVICE_SUBEVENT_SPP_SERVICE_DISCONNECTED:
                con_handle = HCI_CON_HANDLE_INVALID;
                connect_flag = 0;
                break;
            default:
                break;
            }
            break;
        case RFCOMM_DATA_PACKET:
            // LOG << "RECV: " << size << LOG_END;

            // NOTE: This is not "thread-safe" w.r.t. receiving data in this IRQ
            // handler before the main loop has a chance to read it, but we're
            // acknowledging and ignoring this for now.

            // Copy the data into the buffer
            std::copy(packet, packet + size, rx_buffer.begin());
            rx_size = size;
            // Release the semaphore
            sem_release(&rx_sem);
            break;
        default:
            break;
        }
    }

    void heartbeat_handler(struct btstack_timer_source *ts) {
        switch (connect_flag) {
        case 0:
            // Invert the led
            led_on = !led_on;
            cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, led_on);
            break;
        case 1:
            // DO NOT Invert the led
            led_on = true;
            cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, led_on);
            break;
        }

        // Restart timer
        heartbeat.process = &heartbeat_callback;
        btstack_run_loop_set_timer(&heartbeat, kHeartbeatPeriodMs);
        btstack_run_loop_add_timer(&heartbeat);
    }
};

BleImpl g_impl;

static void hci_event_callback(uint8_t packet_type, uint16_t channel,
                               uint8_t *packet, uint16_t size) {
    g_impl.stack_event_packet_handler(packet_type, channel, packet, size);
}

static void heartbeat_callback(struct btstack_timer_source *ts) {
    g_impl.heartbeat_handler(ts);
}

static void packet_callback(uint8_t packet_type, uint16_t channel,
                            uint8_t *packet, uint16_t size) {
    g_impl.packet_handler(packet_type, channel, packet, size);
}

static void nordic_can_send(void *context) {
    UNUSED(context);
    g_impl.can_send_handler();
}
}  // namespace

// Can't use the actual `Transport::TransportImpl` because we need to bind
// callbacks to raw function pointers, hence the namespaced `BleImpl` struct.
struct Transport::TransportImpl {};

Transport::Transport() : impl_(nullptr) {}

Transport::~Transport() {}

void Transport::initialize() {
    // Initialize the BLE implementation
    g_impl.initialize();

    // Initialize CYW43 driver architecture
    if (cyw43_arch_init()) {
        // Ruh-roh
        // LOG << "CYW43 architecture initialization failed" << LOG_END;
        return;
    }
    // LOG << "CYW43 architecture initialized" << LOG_END;
    // Initialize Logical Link Control and Adaptation Protocol layer
    l2cap_init();
    // Initialize Security Manager Protocol layer
    sm_init();

    // Setup packet handler to inform about BTstack state
    g_impl.hci_event_callback_registration.callback = &hci_event_callback;
    hci_add_event_handler(&g_impl.hci_event_callback_registration);

    // Setup ATT server db attribute database created by compile-gatt.py
    att_server_init(profile_data, NULL, NULL);
    // Register packet handler for ATT server events
    att_server_register_packet_handler(hci_event_callback);

    // Setup Nordic SPP service
    nordic_spp_service_server_init(&packet_callback);

    // setup advertisements
    uint16_t adv_int_min = 0x0030;
    uint16_t adv_int_max = 0x0030;
    uint8_t adv_type = 0;
    bd_addr_t null_addr;
    memset(null_addr, 0, 6);
    gap_advertisements_set_params(adv_int_min, adv_int_max, adv_type, 0,
                                  null_addr, 0x07, 0x00);
    gap_advertisements_set_data(adv_data_len, (uint8_t *)adv_data);
    gap_advertisements_enable(1);

    // Set one-shot btstack timer
    g_impl.heartbeat.process = &heartbeat_callback;
    btstack_run_loop_set_timer(&g_impl.heartbeat, kHeartbeatPeriodMs);
    btstack_run_loop_add_timer(&g_impl.heartbeat);

    // Turn on bluetooth
    hci_power_control(HCI_POWER_ON);
}

void Transport::send(const std::span<uint8_t> &data) { g_impl.send(data); }

std::span<uint8_t> Transport::receive(std::span<uint8_t> buffer) {
    return g_impl.receive(buffer);
}

}  // namespace transport
}  // namespace network
}  // namespace emb
