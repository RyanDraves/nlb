#include "emb/yaal/pio/blink.hpp"

namespace emb {
namespace yaal {

// Create dummy host implementations for the Blink program

struct BlinkProgram::BlinkProgramImpl {
    // Dummy implementation
};

BlinkProgram::BlinkProgram(uint8_t frequency)
    : impl_(nullptr), frequency_(frequency) {}

void BlinkProgram::run() {}

void BlinkProgram::pass_data(const std::span<uint8_t> &data) {
    // Not implemented
}

std::span<uint8_t> BlinkProgram::read_data(std::span<uint8_t> buffer) {
    // Not implemented
    return buffer;
}

void BlinkProgram::stop() {}

}  // namespace yaal
}  // namespace emb
