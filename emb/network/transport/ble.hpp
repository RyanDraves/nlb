#pragma once

#include <cinttypes>
#include <span>

namespace emb {
namespace network {
namespace transport {

class Ble {
  public:
    Ble();
    ~Ble();

    void initialize();

    void send(const std::span<uint8_t> &data);

    std::span<uint8_t> receive(std::span<uint8_t> buffer);

  private:
    struct BleImpl;
    BleImpl *impl_;
};

}  // namespace transport
}  // namespace network
}  // namespace emb
