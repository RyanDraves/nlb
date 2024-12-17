#pragma once

#include <cinttypes>
#include <span>

namespace emb {
namespace network {
namespace transport {

class Ble {
  public:
    static Ble &getInstance() {
        static Ble instance;
        return instance;
    }

    void initialize();

    void send(const std::span<uint8_t> &data);

    std::span<uint8_t> receive(std::span<uint8_t> buffer);

  private:
    Ble();
    ~Ble();

    Ble(const Ble &) = delete;
    Ble &operator=(const Ble &) = delete;

    struct BleImpl;
    BleImpl *impl_;

    bool initialized_ = false;
};

}  // namespace transport
}  // namespace network
}  // namespace emb
