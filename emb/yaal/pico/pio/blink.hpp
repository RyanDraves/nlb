#pragma once

#include "emb/yaal/pico/pio_program.hpp"

#include "hardware/clocks.h"
#include "hardware/pio.h"

#include "emb/yaal/pico/pio/blink.pio.h"

namespace emb {
namespace yaal {
namespace pico {

class BlinkProgram : public Program {
  public:
    BlinkProgram(uint8_t frequency) : frequency_(frequency) {
        uint8_t pin = PICO_DEFAULT_LED_PIN;

        bool rc = pio_claim_free_sm_and_add_program_for_gpio_range(
            &blink_program, &pio_, &sm_, &offset_, pin, 1,
            true /* set_gpio_base */);

        pio_gpio_init(pio_, pin);
        pio_sm_set_consecutive_pindirs(pio_, sm_, pin, 1, true /* is_out */);
        pio_sm_config c = blink_program_get_default_config(offset_);
        sm_config_set_set_pins(&c, pin, 1);
        pio_sm_init(pio_, sm_, offset_, &c);
    };
    ~BlinkProgram() = default;

    void run() override {
        pio_sm_set_enabled(pio_, sm_, true);
        // PIO counter program takes 3 more cycles in total than we pass as
        // input (wait for n + 1; mov; jmp)
        pio_->txf[sm_] = (clock_get_hz(clk_sys) / (2 * frequency_)) - 3;
    }

    void pass_data(const std::span<uint8_t> &data) override {
        // Not implemented
    }

    std::span<uint8_t> read_data(std::span<uint8_t> buffer) override {
        // Not implemented
        return buffer;
    }

    void stop() override { pio_sm_set_enabled(pio_, sm_, false); }

  private:
    uint8_t frequency_;
};

}  // namespace pico
}  // namespace yaal
}  // namespace emb
