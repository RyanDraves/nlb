#include "emb/slic/hc_sr04.hpp"

#include "emb/yaal/gpio.hpp"
#include "emb/yaal/timer.hpp"

namespace emb {
namespace slic {

HcSr04::HcSr04(yaal::Gpio &trigger, yaal::Gpio &echo)
    : trigger_(trigger), echo_(echo) {}

HcSr04::~HcSr04() {}

uint32_t HcSr04::get_distance_mm() {
    // Trigger the sensor
    trigger_.set(true);
    yaal::sleep_us(10);
    trigger_.set(false);

    // Wait for the echo to go high for up to kMaxDistanceUs
    uint32_t timeout_us = yaal::get_time_us() + kMaxDistanceUs;
    while (!echo_.read()) {
        if (yaal::get_time_us() > timeout_us) {
            return 0;
        }
    }

    // Start the timer
    uint32_t echo_start_us = yaal::get_time_us();
    timeout_us = echo_start_us + kMaxDistanceUs;

    // Wait for the echo to go low for up to kMaxDistanceUs
    while (echo_.read()) {
        if (yaal::get_time_us() > timeout_us) {
            // Assume the result is max range if the echo pin is still high
            break;
        }
    }

    // Stop the timer
    uint32_t echo_end_us = yaal::get_time_us();

    // Calculate the distance
    uint32_t pulse_width_us = echo_end_us - echo_start_us;
    // Calculated from the assumed speed of sound in air at sea level (~340
    // m/s); pulse. Constant provided in the datasheet.
    uint32_t distance_mm = pulse_width_us * 1000 / 5800;

    return distance_mm;
}

}  // namespace slic
}  // namespace emb
