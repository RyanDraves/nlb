#include "emb/yaal/pio.hpp"

namespace emb {
namespace yaal {

// Create dummy host implementations for the PIO class

struct Pio::PioImpl {};

Pio::Pio(Program program, std::span<const uint8_t> pins)
    : program_(program), pins_(pins), impl_(nullptr) {}

Pio::~Pio() {}

void Pio::run() {}

void Pio::pass_data(const std::span<uint8_t> &data) {}

std::span<uint8_t> Pio::read_data(std::span<uint8_t> buffer) { return buffer; }

void Pio::stop() {}

}  // namespace yaal
}  // namespace emb
