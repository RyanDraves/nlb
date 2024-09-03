#include "hardware/flash.h"

#include "emb/yaal/flash.hpp"

namespace emb {
namespace yaal {

const uint8_t *get_flash_ptr(uint32_t addr) {
    // The flash is memory-mapped at XIP_BASE
    return (const uint8_t *)(XIP_BASE + addr);
}

}  // namespace yaal
}  // namespace emb
