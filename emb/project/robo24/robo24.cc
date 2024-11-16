#include <cinttypes>
#include <vector>

#include "emb/project/base/base_bh.hpp"
#include "emb/project/robo24/robo24_bh.hpp"

#include "emb/slic/hc_sr04.hpp"
#include "emb/yaal/gpio.hpp"
#include "emb/yaal/timer.hpp"

namespace emb {
namespace project {
namespace robo24 {

struct Robo24::Robo24Impl {
    Robo24Impl(uint8_t trigger_pin, uint8_t echo_pin)
        : trigger(trigger_pin), echo(echo_pin), hc_sr04(trigger, echo) {
        trigger.set_mode(yaal::Mode::OUTPUT);
        echo.set_mode(yaal::Mode::INPUT);
    }

    yaal::Gpio trigger;
    yaal::Gpio echo;
    slic::HcSr04 hc_sr04;
};

Robo24::Robo24() : impl_(new Robo24Impl(1 /* trigger */, 0 /* echo */)) {}

Robo24::~Robo24() { delete impl_; }

DistanceMeasurement Robo24::get_measurement(const base::Ping &ping) {
    DistanceMeasurement meas;

    /* This simple implementation makes a few assumptions:
    - The driver is synchronous and blocking (i.e. echo pulses could never
    overlap so long as the signal bounces once)
    - That it's O.K. to ignore the 60ms timeout in the HC-SR04 datasheet
    */

    meas.distance_mm = impl_->hc_sr04.get_distance_mm();
    meas.timestamp_ms = yaal::get_time_ms();

    return meas;
}

}  // namespace robo24
}  // namespace project
}  // namespace emb
