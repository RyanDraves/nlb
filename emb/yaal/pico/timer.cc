#include "emb/yaal/timer.hpp"

#include "hardware/timer.h"
#include "pico/stdlib.h"

namespace emb {

namespace yaal {

void sleep_us(uint32_t us) {
    // Sleep for a number of microseconds
    // Make sure to use the `sleep_us` function from `pico/stdlib.h`
    ::sleep_us(us);
}

uint64_t get_time_us() {
    // Get the time since boot in microseconds
    return to_us_since_boot(get_absolute_time());
}

uint32_t get_time_ms() {
    // Get the time since boot in milliseconds
    return to_ms_since_boot(get_absolute_time());
}

uint32_t get_time_s() {
    // Get the time since boot in seconds
    return get_time_us() / 1'000'000;
}

}  // namespace yaal

}  // namespace emb
