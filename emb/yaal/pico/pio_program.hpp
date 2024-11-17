#pragma once

#include <cinttypes>
#include <span>

#include "hardware/pio.h"

namespace emb {
namespace yaal {
namespace pico {

class Program {
  public:
    Program() = default;
    ~Program() = default;

    virtual void run() = 0;
    virtual void pass_data(const std::span<uint8_t> &data) = 0;
    virtual std::span<uint8_t> read_data(std::span<uint8_t> buffer) = 0;
    virtual void stop() = 0;

  protected:
    PIO pio_;
    uint sm_;
    uint offset_;
};

}  // namespace pico
}  // namespace yaal
}  // namespace emb
