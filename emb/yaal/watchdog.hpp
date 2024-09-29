#pragma once

namespace emb {
namespace yaal {

// Reset via the watchdog immediately
[[noreturn]] void force_watchdog_reset();

}  // namespace yaal
}  // namespace emb
