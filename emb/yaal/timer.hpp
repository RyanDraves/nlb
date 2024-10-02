#include <cinttypes>

namespace emb {
namespace yaal {

// I wanted to make a joke about this function,
//
//
//
//
//
//       but I couldn't get the timing right.
//
// Anyways `uint32_t` will overflow after 71 minutes.
// If you ask to sleep for longer than that, you deserve
// the overflow and should consider it a spurious wake-up.
void sleep_us(uint32_t us);

// Get time since boot in microseconds
//
// This function will overflow after 584,000 years.
uint64_t get_time_us();

// Get time since boot in milliseconds
//
// This function will overflow after 49 days.
// If you have a device that is on for longer than that,
// congrats I'm jealous, go use `get_time_s`.
uint32_t get_time_ms();

// Get time since boot in seconds
//
// This function will overflow after 136 years.
// If you have a device that is on for longer than that,
// I won't be around to care.
uint32_t get_time_s();

}  // namespace yaal
}  // namespace emb
