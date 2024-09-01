#pragma once

#include <inttypes.h>

namespace emb {
namespace yaal {

// Get a pointer to the flash memory, 0-indexed
const uint8_t *get_flash_ptr(uint32_t addr);

}  // namespace yaal
}  // namespace emb
