#include "emb/yaal/flash.hpp"

namespace emb {
namespace yaal {

namespace {
uint8_t *g_arena = new uint8_t[1024 * 1024 * 2];
}  // namespace

const uint8_t *get_flash_ptr(uint32_t addr) { return g_arena + addr; }

}  // namespace yaal
}  // namespace emb
