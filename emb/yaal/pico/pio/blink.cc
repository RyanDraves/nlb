#include "emb/yaal/pio/blink.hpp"

#include "hardware/clocks.h"
#include "hardware/pio.h"

#include "emb/yaal/pico/pio/blink.pio.h"

namespace emb {
namespace yaal {

struct BlinkProgram::BlinkProgramImpl {
    PIO pio;
    uint sm;
    uint offset;
};

BlinkProgram::BlinkProgram(uint8_t frequency)
    : impl_(new BlinkProgramImpl), frequency_(frequency) {
    uint8_t pin = PICO_DEFAULT_LED_PIN;

    bool rc = pio_claim_free_sm_and_add_program_for_gpio_range(
        &blink_program, &impl_->pio, &impl_->sm, &impl_->offset, pin, 1,
        true /* set_gpio_base */);

    pio_gpio_init(impl_->pio, pin);
    pio_sm_set_consecutive_pindirs(impl_->pio, impl_->sm, pin, 1,
                                   true /* is_out */);
    pio_sm_config c = blink_program_get_default_config(impl_->offset);
    sm_config_set_set_pins(&c, pin, 1);
    pio_sm_init(impl_->pio, impl_->sm, impl_->offset, &c);
}

void BlinkProgram::run() {
    pio_sm_set_enabled(impl_->pio, impl_->sm, true);
    // PIO counter program takes 3 more cycles in total than we pass as
    // input (wait for n + 1; mov; jmp)
    impl_->pio->txf[impl_->sm] = (clock_get_hz(clk_sys) / (2 * frequency_)) - 3;
}

void BlinkProgram::pass_data(const std::span<uint8_t> &data) {
    // Not implemented
}

std::span<uint8_t> BlinkProgram::read_data(std::span<uint8_t> buffer) {
    // Not implemented
    return buffer;
}

void BlinkProgram::stop() { pio_sm_set_enabled(impl_->pio, impl_->sm, false); }

}  // namespace yaal
}  // namespace emb
