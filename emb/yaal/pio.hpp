#pragma once

#include <cinttypes>
#include <span>

namespace emb {
namespace yaal {

enum class Program : uint8_t {
    BLINK_GPIO = 0,
};

class Pio {
  public:
    Pio(Program program, std::span<const uint8_t> pins);
    ~Pio();

    /**
     * Run the PIO state machine
     */
    void run();

    /**
     * Pass data to the TX FIFO
     */
    void pass_data(const std::span<uint8_t> &data);

    /**
     * Read data from the RX FIFO
     */
    std::span<uint8_t> read_data(std::span<uint8_t> buffer);

    /**
     * Stop the PIO state machine
     */
    void stop();

  private:
    Program program_;
    std::span<const uint8_t> pins_;

    struct PioImpl;
    PioImpl *impl_;
};

}  // namespace yaal
}  // namespace emb
