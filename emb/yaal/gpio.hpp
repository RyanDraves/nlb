#pragma once

#include <cinttypes>

namespace emb {
namespace yaal {

enum Mode : uint8_t {
    INPUT = 0,
    OUTPUT = 1,
};

class Gpio {
  public:
    Gpio(uint8_t pin);

    void set_mode(Mode mode);
    Mode get_mode() const;

    void pulse(uint16_t duration_us);

    void set(bool high);
    virtual bool read() const;

  private:
    uint8_t pin_;
};

}  // namespace yaal
}  // namespace emb
