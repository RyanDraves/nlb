#include "emb/project/base/base_bh.hpp"
#include "emb/project/bootloader/bootloader_bh.hpp"
#include "emb/yaal/flash.hpp"

#include "hardware/flash.h"
#include "hardware/gpio.h"
#include "hardware/structs/nvic.h"
#include "hardware/structs/scb.h"
#include "hardware/structs/systick.h"
#include "pico/stdlib.h"

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

// 2KB of stack, so keep our buffer small. We can borrow some stack from
// core 1's 2KB, but our flash logic is simple and requires sector alignment
// (can't write to multiple sectors at once), so 1kB each will suffice.
static const uint32_t kBufferSize = 1024;

void read_buffer(uint8_t buffer[kBufferSize], uint32_t addr, uint32_t size) {
    memcpy(buffer, emb::yaal::get_flash_ptr(addr), size);
}

int main() {
    // Read the system flash page
    auto buffer = emb::yaal::flash_sector_read(0);
    emb::project::bootloader::SystemFlashPage system_flash_page =
        emb::project::bootloader::SystemFlashPage::deserialize(buffer).first;

    // Increment the boot count
    system_flash_page.boot_count++;

    // Blink the LED to indicate the bootloader is running
    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);

    // Lighting sequence
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

    uint8_t buffer_a[kBufferSize];
    uint8_t buffer_b[kBufferSize];
    if (system_flash_page.new_image_flashed) {
        // Do a "double-shuffle" to move the new image from B to A
        // and the old image from A to B
        uint32_t addr_a = emb::yaal::kAppAddrA;
        uint32_t addr_b = emb::yaal::kAppAddrB;

        // Start with the LED on
        gpio_put(PICO_DEFAULT_LED_PIN, 1);

        bool led_on = false;
        while (addr_b < emb::yaal::kAppAddrB + system_flash_page.image_size_b) {
            read_buffer(buffer_a, addr_a, kBufferSize);
            read_buffer(buffer_b, addr_b, kBufferSize);
            emb::yaal::flash_write(addr_b, buffer_a);
            emb::yaal::flash_write(addr_a, buffer_b);
            addr_a += kBufferSize;
            addr_b += kBufferSize;

            // Toggle the LED every 10KB
            if ((addr_b - emb::yaal::kAppAddrB) % 10240 == 0) {
                gpio_put(PICO_DEFAULT_LED_PIN, led_on);
                led_on = !led_on;
            }
        }

        // Make sure we copied all of image A to B
        while (addr_a < emb::yaal::kAppAddrA + system_flash_page.image_size_a) {
            read_buffer(buffer_a, addr_a, kBufferSize);
            emb::yaal::flash_write(addr_b, buffer_a);
            addr_a += kBufferSize;
            addr_b += kBufferSize;
        }

        // Ensure the LED is off
        gpio_put(PICO_DEFAULT_LED_PIN, 0);

        // Update the system flash page
        system_flash_page.new_image_flashed = 0;
        uint32_t tmp = system_flash_page.image_size_a;
        system_flash_page.image_size_a = system_flash_page.image_size_b;
        system_flash_page.image_size_b = tmp;
    }

    // Write the system flash page back to flash
    system_flash_page.serialize(buffer_a);
    emb::yaal::flash_sector_write(0, buffer_a);

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
