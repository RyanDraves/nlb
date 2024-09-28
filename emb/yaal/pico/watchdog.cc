#include "emb/yaal/watchdog.hpp"

#include "hardware/watchdog.h"

namespace emb {
namespace yaal {

[[noreturn]] void force_watchdog_reset() {
    // Reboot via the watchdog
    watchdog_reboot(0, 0, 0);

    // Wait for the watchdog to reset the system
    while (true) {
        tight_loop_contents();
    }
}

}  // namespace yaal
}  // namespace emb
