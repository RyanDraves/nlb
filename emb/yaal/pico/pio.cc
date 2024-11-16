#include "emb/yaal/pio.hpp"

#include <optional>

#include "hardware/pio.h"

#include "emb/yaal/pico/pio/blink.hpp"
#include "emb/yaal/pico/pio_program.hpp"

namespace emb {
namespace yaal {

struct Pio::PioImpl {
    pico::Program *program;
};

Pio::Pio(Program program, std::span<const uint8_t> pins)
    : program_(program), pins_(pins), impl_(new PioImpl(nullptr)) {
    if (program_ == Program::BLINK_GPIO) {
        impl_->program = new pico::BlinkProgram(1 /* frequency */);
    }
}

Pio::~Pio() {}

void Pio::run() {
    if (!impl_->program) {
        return;
    }
    impl_->program->run();
}

void Pio::pass_data(const std::span<uint8_t> &data) {
    if (!impl_->program) {
        return;
    }

    impl_->program->pass_data(data);
}

std::span<uint8_t> Pio::read_data(std::span<uint8_t> buffer) {
    if (!impl_->program) {
        return buffer;
    }

    return impl_->program->read_data(buffer);
}

void Pio::stop() {
    if (!impl_->program) {
        return;
    }

    impl_->program->stop();
}

}  // namespace yaal
}  // namespace emb
