#pragma once

#include "emb/yaal/pio.hpp"

namespace emb {
namespace yaal {

class BlinkProgram : public PioProgram {
  public:
    BlinkProgram(uint8_t frequency);
    ~BlinkProgram() = default;

    void run() override;

    void pass_data(const std::span<uint8_t> &data) override;

    std::span<uint8_t> read_data(std::span<uint8_t> buffer) override;

    void stop() override;

  private:
    struct BlinkProgramImpl;
    BlinkProgramImpl *impl_;
    uint8_t frequency_;
};

}  // namespace yaal
}  // namespace emb
