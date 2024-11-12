#include "emb/yaal/timer.hpp"
#include "emb/yaal/host/timer.hpp"

#include <chrono>
#include <thread>

namespace emb {

namespace yaal {

namespace {
// Sneaky global variable to capture the time at boot
auto g_boot_time = std::chrono::steady_clock::now();
}  // namespace

void sleep_us(uint32_t us) {
    // Sleep for a number of microseconds
    std::this_thread::sleep_for(std::chrono::microseconds(us));
}

uint64_t get_time_us() {
    // Get the time since boot in microseconds
    auto now = std::chrono::steady_clock::now();
    return std::chrono::duration_cast<std::chrono::microseconds>(now -
                                                                 g_boot_time)
        .count();
}

uint32_t get_time_ms() {
    // Get the time since boot in milliseconds
    return get_time_us() / 1'000;
}

uint32_t get_time_s() {
    // Get the time since boot in seconds
    return get_time_us() / 1'000'000;
}

void move_clock(std::chrono::duration<uint64_t, std::micro> duration) {
    // Move the clock back in time; a clock read will effectively be `duration`
    // farther apart from the boot time
    g_boot_time -= duration;
}

}  // namespace yaal

}  // namespace emb
