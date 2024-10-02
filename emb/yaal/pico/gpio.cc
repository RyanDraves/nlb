#include "emb/yaal/gpio.hpp"

#include "hardware/gpio.h"

#include "pico/stdlib.h"

namespace emb {
namespace yaal {

Gpio::Gpio(uint8_t pin) : pin_(pin) {}

void Gpio::set_mode(Mode mode) {
    // Set the mode of the GPIO pin
    gpio_init(pin_);
    switch (mode) {
    case Mode::INPUT:
        gpio_set_dir(pin_, GPIO_IN);
        break;
    case Mode::OUTPUT:
        gpio_set_dir(pin_, GPIO_OUT);
        break;
    }
}

Mode Gpio::get_mode() const {
    // Get the mode of the GPIO pin
    bool is_out = gpio_get_dir(pin_) == GPIO_OUT;
    return is_out ? Mode::OUTPUT : Mode::INPUT;
}

void Gpio::pulse(uint16_t duration_us) {
    // Pulse the GPIO pin for a duration
    gpio_put(pin_, true);
    sleep_us(duration_us);
    gpio_put(pin_, false);
}

void Gpio::set(bool high) {
    // Set the GPIO pin to high or low
    gpio_put(pin_, high);
}

bool Gpio::read() const {
    // Read the GPIO pin
    return gpio_get(pin_);
}

}  // namespace yaal
}  // namespace emb
