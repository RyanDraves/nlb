#include "emb/yaal/flash.hpp"

#include "emb/project/bootloader/bootloader_bh.hpp"
#include <string.h>

/*
Mimic the flash memory of the Pico
*/

namespace emb {
namespace yaal {

namespace {
uint8_t *g_arena = new uint8_t[project::bootloader::kPicoFlashSize];

// The start address of the scratchpad
constexpr uint32_t g_sector_start_addr =
    (project::bootloader::kPicoFlashSize) -
    (project::bootloader::kNumSectors * 4096);
}  // namespace

const uint32_t kAppAddrA = project::bootloader::kPicoAppAddrA;
const uint32_t kAppAddrB = project::bootloader::kPicoAppAddrB;

const uint8_t *get_flash_ptr(uint32_t addr) { return g_arena + addr; }

uint32_t get_flash_sector_addr(uint8_t sector) {
    return g_sector_start_addr + (sector * 4096);
}

void flash_write(uint32_t addr, std::span<const uint8_t> data) {
    uint32_t sector_start = addr & ~4095;
    uint32_t sector_offset = addr - sector_start;

    // Copy the data into the sector
    memcpy(g_arena + sector_start + sector_offset, data.data(), data.size());
}

void flash_sector_write(uint8_t sector, std::span<const uint8_t> data) {
    // A sector read should give back the same data that was written,
    // so write a simple [size_of_data, data] to the sector
    uint16_t size = data.size();

    uint32_t sector_addr = get_flash_sector_addr(sector);

    // Erase the sector by writing 0xFF to it
    memset(g_arena + sector_addr, 0xFF, 4096);

    // Copy the size and data into the buffer
    memcpy(g_arena + sector_addr, &size, 2);
    memcpy(g_arena + sector_addr + 2, data.data(), size);
}

std::span<const uint8_t> flash_sector_read(uint8_t sector) {
    uint32_t sector_addr = get_flash_sector_addr(sector);

    uint16_t size;
    memcpy(&size, g_arena + sector_addr, 2);

    return {g_arena + sector_addr + 2, size};
}

}  // namespace yaal
}  // namespace emb
