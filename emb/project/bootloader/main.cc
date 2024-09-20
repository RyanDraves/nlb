#include "emb/network/serialize/bh_cobs.hpp"
#include "emb/network/transport/serial.hpp"
#include "emb/project/base/base_bh.hpp"
#include "emb/project/bootloader/bootloader_bh.hpp"
#include "emb/yaal/flash.hpp"

#include "pico/stdlib.h"

#include <span>

int main() {
    // Initialize the serial transport
    emb::network::transport::Serial transport;
    emb::network::serialize::BhCobs serializer;

    uint8_t tx_buffer[1024];

    // Read the system flash page
    auto buffer = emb::yaal::flash_sector_read(0);
    emb::project::bootloader::SystemFlashPage system_flash_page =
        emb::project::bootloader::SystemFlashPage::deserialize(buffer);

    // Increment the boot count
    system_flash_page.boot_count++;

    // Write the system flash page back to flash
    emb::yaal::flash_sector_write(0, system_flash_page.serialize(tx_buffer));

    // Jump to the application
    uint32_t app_addr = reinterpret_cast<uint32_t>(emb::yaal::get_flash_ptr(
        system_flash_page.boot_side == 0 ? emb::yaal::kAppAddrA
                                         : emb::yaal::kAppAddrB));
    uint32_t app_stack_pointer = *(uint32_t *)app_addr;
    typedef void (*app_entry_t)(void);
    app_entry_t app_entry = (app_entry_t) * (uint32_t *)(app_addr + 4);

    // Set the main stack pointer
    // Equivalent to __set_MSP(app_stack_pointer);
    // https://github.com/raspberrypi/pico-sdk/blob/efe2103f9b28458a1615ff096054479743ade236/src/rp2_common/cmsis/stub/CMSIS/Core/Include/m-profile/cmsis_gcc_m.h#L309
    __asm volatile("msr msp, %0" ::"r"(app_stack_pointer) :);
    // Jump to the application
    app_entry();

    // We should never get here
    emb::project::base::LogMessage log_message;

    log_message.message =
        "Bootloader failed. Boot side: " +
        std::to_string(system_flash_page.boot_side) +
        "\nBoot count: " + std::to_string(system_flash_page.boot_count);

    // Encode the outgoing message;
    // offset by one to leave room for the message ID
    auto [serialized, frame_padding] = serializer.serialize(
        log_message, std::span(tx_buffer + 1, sizeof(tx_buffer) - 1));
    // Add the message ID
    tx_buffer[frame_padding] = 0x00;
    // Add back our +1 offset
    auto framed = serializer.frame(std::span(tx_buffer, serialized.size() + 1));
    while (true) {
        transport.send(framed);
        sleep_ms(1000);
    }
}
