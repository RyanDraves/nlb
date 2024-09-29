#include "emb/yaal/watchdog.hpp"

#include <cstdlib>

namespace emb {
namespace yaal {

[[noreturn]] void force_watchdog_reset() { exit(1); }

}  // namespace yaal
}  // namespace emb
