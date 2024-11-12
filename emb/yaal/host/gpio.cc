#include "emb/yaal/gpio.hpp"

namespace emb {
namespace yaal {

Gpio::Gpio(uint8_t pin) : pin_(pin) {}

void Gpio::set_mode(Mode mode) { return; }

Mode Gpio::get_mode() const { return Mode::INPUT; }

void Gpio::pulse(uint16_t duration_us) { return; }

void Gpio::set(bool high) { return; }

bool Gpio::read() const { return false; }

}  // namespace yaal
}  // namespace emb
