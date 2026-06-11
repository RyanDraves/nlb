#include "emb/project/base/base_bh.hpp"
#include "emb/project/bootloader/bootloader_bh.hpp"
#include "emb/yaal/flash.hpp"

#include "hardware/flash.h"
#include "hardware/gpio.h"
#include "hardware/structs/nvic.h"
#include "hardware/structs/scb.h"
#include "hardware/structs/systick.h"
#include "pico/stdio_usb.h"
#include "pico/stdlib.h"

#include <cstdio>
#include <span>

/* Borrowed from
   https://github.com/usedbytes/rp2040-serial-bootloader/
*/
static void disable_interrupts() {
    systick_hw->csr &= (volatile uint32_t) ~1;

    nvic_hw->icer = (volatile uint32_t)0xFFFFFFFF;
    nvic_hw->icpr = (volatile uint32_t)0xFFFFFFFF;
}

static void reset_peripherals(void) {
    reset_block(~(RESETS_RESET_IO_QSPI_BITS | RESETS_RESET_PADS_QSPI_BITS |
                  RESETS_RESET_SYSCFG_BITS | RESETS_RESET_PLL_SYS_BITS));
}

static void jump_to_vtor(uint32_t vtor) {
    // Derived from the Leaf Labs Cortex-M3 bootloader.
    // Copyright (c) 2010 LeafLabs LLC.
    // Modified 2021 Brian Starkey <stark3y@gmail.com>
    // Originally under The MIT License
    uint32_t reset_vector = *(volatile uint32_t *)(vtor + 0x04);

    scb_hw->vtor = (volatile uint32_t)(vtor);

    asm volatile("msr msp, %0" ::"g"(*(volatile uint32_t *)vtor));
    asm volatile("bx %0" ::"r"(reset_vector));
}
/* End borrowed code
 */

// We'll copy over one entire sector at a time. The flash implementation will
// erase data in the same sector that we're writing to, so a read shouldn't
// interleave with a write within the same sector.
static uint8_t g_buffer[FLASH_SECTOR_SIZE];

void read_buffer(uint8_t buffer[FLASH_SECTOR_SIZE], uint32_t addr,
                 uint32_t size) {
    memcpy(buffer, emb::yaal::get_flash_ptr(addr), size);
}

int main() {
    // Read the system flash page
    auto buffer = emb::yaal::flash_sector_read(0);
    emb::project::bootloader::SystemFlashPage system_flash_page =
        emb::project::bootloader::SystemFlashPage::deserialize(buffer).first;

    // Increment the boot count
    system_flash_page.boot_count++;

    // Initialize USB serial for progress output
    stdio_init_all();

    // Blink the LED to indicate the bootloader is running
    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);

    // Initial lighting sequence
    gpio_put(PICO_DEFAULT_LED_PIN, 1);
    sleep_ms(50);
    gpio_put(PICO_DEFAULT_LED_PIN, 0);
    sleep_ms(50);
    gpio_put(PICO_DEFAULT_LED_PIN, 1);
    sleep_ms(50);
    gpio_put(PICO_DEFAULT_LED_PIN, 0);
    sleep_ms(25);
    gpio_put(PICO_DEFAULT_LED_PIN, 1);
    sleep_ms(13);
    gpio_put(PICO_DEFAULT_LED_PIN, 0);
    sleep_ms(12);
    gpio_put(PICO_DEFAULT_LED_PIN, 1);
    sleep_ms(50);
    gpio_put(PICO_DEFAULT_LED_PIN, 0);

    if (system_flash_page.new_image_flashed) {
        // Give the host a moment to attach to the freshly-enumerated USB
        // serial port so it can observe the swap progress
        for (int i = 0; i < 200 && !stdio_usb_connected(); i++) {
            sleep_ms(10);
        }
        // Do a "double-shuffle" to move the new image from B to A
        // and the old image from A to B
        uint32_t addr_a = emb::yaal::kAppAddrA;
        uint32_t addr_b = emb::yaal::kAppAddrB;

        // Progress, in bytes processed of the larger image
        uint32_t total = system_flash_page.image_size_a >
                                 system_flash_page.image_size_b
                             ? system_flash_page.image_size_a
                             : system_flash_page.image_size_b;

        // Start with the LED on
        gpio_put(PICO_DEFAULT_LED_PIN, 1);
        bool led_on = true;

        // Alternate fast and slow blinks during the swap so the pattern is
        // aperiodic, unlike the application's steady blinking. Toggle
        // intervals are in sectors (~100ms each to swap).
        constexpr uint32_t kBlinkPattern[] = {1, 1, 1, 1, 1, 1, 4, 4};
        constexpr size_t kBlinkPatternSize =
            sizeof(kBlinkPattern) / sizeof(kBlinkPattern[0]);
        uint32_t sectors = 0;
        uint32_t next_toggle = 1;
        size_t pattern_idx = 0;
        auto tick_led = [&]() {
            sectors++;
            if (sectors >= next_toggle) {
                led_on = !led_on;
                gpio_put(PICO_DEFAULT_LED_PIN, led_on);
                next_toggle += kBlinkPattern[pattern_idx];
                pattern_idx = (pattern_idx + 1) % kBlinkPatternSize;
            }
        };
        while (addr_b < emb::yaal::kAppAddrB + system_flash_page.image_size_b) {
            read_buffer(g_buffer, addr_a, FLASH_SECTOR_SIZE);
            emb::yaal::flash_write(
                addr_a,
                std::span(emb::yaal::get_flash_ptr(addr_b), FLASH_SECTOR_SIZE));
            emb::yaal::flash_write(addr_b, g_buffer);
            addr_a += FLASH_SECTOR_SIZE;
            addr_b += FLASH_SECTOR_SIZE;

            // Report progress every 4 sectors
            if ((addr_b - emb::yaal::kAppAddrB) % (4 * FLASH_SECTOR_SIZE) ==
                0) {
                printf("FLASH %lu %lu\n", addr_b - emb::yaal::kAppAddrB,
                       total);
            }

            tick_led();
        }

        // Make sure we copied all of image A to B
        while (addr_a < emb::yaal::kAppAddrA + system_flash_page.image_size_a) {
            read_buffer(g_buffer, addr_a, FLASH_SECTOR_SIZE);
            emb::yaal::flash_write(addr_b, g_buffer);
            addr_a += FLASH_SECTOR_SIZE;
            addr_b += FLASH_SECTOR_SIZE;

            // Report progress every 4 sectors
            if ((addr_b - emb::yaal::kAppAddrB) % (4 * FLASH_SECTOR_SIZE) ==
                0) {
                printf("FLASH %lu %lu\n", addr_b - emb::yaal::kAppAddrB,
                       total);
            }

            tick_led();
        }

        printf("FLASH %lu %lu\nDONE\n", total, total);
        stdio_flush();
        // Give USB a moment to drain the progress output to the host
        sleep_ms(50);

        // Ensure the LED is off
        gpio_put(PICO_DEFAULT_LED_PIN, 0);

        // Update the system flash page
        system_flash_page.new_image_flashed = 0;
        uint32_t tmp = system_flash_page.image_size_a;
        system_flash_page.image_size_a = system_flash_page.image_size_b;
        system_flash_page.image_size_b = tmp;
    }

    // Write the system flash page back to flash
    auto page_buffer = system_flash_page.serialize(g_buffer);
    emb::yaal::flash_sector_write(0, page_buffer);

    // Jump to the application
    uint32_t app_addr = XIP_BASE + emb::yaal::kAppAddrA;
    disable_interrupts();
    reset_peripherals();
    jump_to_vtor(app_addr);

    // We should never get here
    while (1) {
        gpio_put(PICO_DEFAULT_LED_PIN, 0);
        sleep_ms(500);
        gpio_put(PICO_DEFAULT_LED_PIN, 1);
        sleep_ms(500);
    }
}
