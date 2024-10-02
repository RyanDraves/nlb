#pragma once

#include <cinttypes>
#include <span>

namespace emb {
namespace yaal {

extern const uint32_t kAppAddrA;
extern const uint32_t kAppAddrB;

// Get a pointer to the flash memory, 0-indexed
const uint8_t *get_flash_ptr(uint32_t addr);

// Get the address of a flash sector
uint32_t get_flash_sector_addr(uint8_t sector);

// Write data to flash memory
void flash_write(uint32_t addr, std::span<const uint8_t> data);

// Write a sector of data to flash memory.
// This will not preseve the data that was previously in the sector and will
// be written in a format to ensure that a read of the sector will return the
// same data that was written.
void flash_sector_write(uint8_t sector, std::span<const uint8_t> data);

// Read a sector of data from flash memory.
// This will return the data that was written with flash_sector_write, _not_
// the entire sector.
std::span<const uint8_t> flash_sector_read(uint8_t sector);

}  // namespace yaal
}  // namespace emb
