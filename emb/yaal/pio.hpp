#pragma once

#include <cinttypes>
#include <span>

namespace emb {
namespace yaal {

class PioProgram {
  public:
    PioProgram() = default;
    ~PioProgram() = default;

    virtual void run() = 0;
    virtual void pass_data(const std::span<uint8_t> &data) = 0;
    virtual std::span<uint8_t> read_data(std::span<uint8_t> buffer) = 0;
    virtual void stop() = 0;
};

}  // namespace yaal
}  // namespace emb
