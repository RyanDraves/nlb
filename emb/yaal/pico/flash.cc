#include "hardware/flash.h"
#include "hardware/sync.h"
#include <string.h>

#include "emb/project/base/base_bh.hpp"
#include "emb/yaal/flash.hpp"

/*
Pico flash memory layout:

The Pico has 2 MB of flash memory, which is divided into 4kB sectors.
Within each sector are 256 byte pages, which is the minimal write size.
The flash is memory-mapped at XIP_BASE and sectors must be erased
before they can be written to.

We want to keep three things in flash:
- The bootloader
- Two copies of the firmware (A and B "side")
- Allocated space for sectors to read/write from, like a scratchpad

The bootloader is stored at the beginning of flash memory and takes ~24kB, for
which we'll allocate 160kB (it's closer to 150kB if fancier features are added).
The scratchpad is stored at the end of flash memory and takes 32 * 4kB = 128kB.

The firmware is stored in the middle of flash memory, with the two copies
each getting 880 kB of space.

Firmware is compiled to start at image A, so the bootloader will always jump to
image A. When a new image is flashed, it will be written to image B, and then
the bootloader will swap the images and jump to the new image.

These functions will let you write to image A, but don't be surprised if the
system crashes while writing to instructions that are currently being executed.
*/

namespace emb {
namespace yaal {

namespace {
// The start address of the scratchpad
constexpr uint32_t g_sector_start_addr =
    project::base::kPicoFlashSize -
    (project::base::kNumSectors * FLASH_SECTOR_SIZE);

// We'll use this to store a copy of the sector we're working with;
// an un-fun use of RAM
// TODO: Consider tracking which sectors need to be erased and assume
// we're not writing to the same address twice (big assumption?)
uint8_t g_sector_buffer[FLASH_SECTOR_SIZE];
}  // namespace

const uint32_t kAppAddrA = project::base::kPicoAppAddrA;
const uint32_t kAppAddrB = project::base::kPicoAppAddrB;

const uint8_t *get_flash_ptr(uint32_t addr) {
    // The flash is memory-mapped at XIP_BASE
    return (const uint8_t *)(XIP_BASE + addr);
}

uint32_t get_flash_sector_addr(uint8_t sector) {
    return g_sector_start_addr + (sector * FLASH_SECTOR_SIZE);
}

void flash_write(uint32_t addr, std::span<const uint8_t> data) {
    uint32_t sector_start = addr & ~4095;
    uint32_t sector_offset = addr - sector_start;

    // Copy the sector into RAM
    memcpy(g_sector_buffer, get_flash_ptr(sector_start), FLASH_SECTOR_SIZE);

    // Copy the data into the sector
    memcpy(g_sector_buffer + sector_offset, data.data(), data.size());

    auto iterrupt_ctx = save_and_disable_interrupts();

    // Erase the sector
    flash_range_erase(sector_start, FLASH_SECTOR_SIZE);

    // Write the sector back
    flash_range_program(sector_start, g_sector_buffer, FLASH_SECTOR_SIZE);

    restore_interrupts(iterrupt_ctx);
}

void flash_sector_write(uint8_t sector, std::span<const uint8_t> data) {
    // A sector read should give back the same data that was written,
    // so write a simple [size_of_data, data] to the sector
    uint16_t size = data.size();

    uint32_t sector_addr = get_flash_sector_addr(sector);

    // Copy the size and data into the buffer
    memcpy(g_sector_buffer, &size, 2);
    memcpy(g_sector_buffer + 2, data.data(), size);

    auto iterrupt_ctx = save_and_disable_interrupts();

    // Erase the sector
    flash_range_erase(sector_addr, FLASH_SECTOR_SIZE);

    // Write the sector back
    // Save some write time and write the data size rounded up to the nearest
    // 256 (FLASH_PAGE_SIZE) bytes
    flash_range_program(sector_addr, g_sector_buffer,
                        (size + 2 + FLASH_PAGE_SIZE - 1) &
                            ~(FLASH_PAGE_SIZE - 1));

    restore_interrupts(iterrupt_ctx);
}

std::span<const uint8_t> flash_sector_read(uint8_t sector) {
    uint32_t sector_addr = get_flash_sector_addr(sector);

    const uint8_t *data = get_flash_ptr(sector_addr);

    // The first two bytes are the size of the data
    uint16_t size;
    memcpy(&size, data, 2);

    // Limit size to the sector size, in case we read bad data
    if (size > FLASH_SECTOR_SIZE - 2) {
        size = FLASH_SECTOR_SIZE - 2;
    }

    return {data + 2, size};
}

}  // namespace yaal
}  // namespace emb
