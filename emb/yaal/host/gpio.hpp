#include "emb/yaal/gpio.hpp"

namespace emb {
namespace yaal {
namespace host {

class HostGpio : public Gpio {
  public:
    HostGpio(uint8_t pin) : Gpio(pin) {}

    void set_level(bool high) { level_ = high; }

    bool read() const override { return level_; }

  private:
    bool level_;
};

}  // namespace host
}  // namespace yaal
}  // namespace emb
