#pragma once

#include <cinttypes>
#include <span>

namespace emb {
namespace network {
namespace transport {

class Serial {
  public:
    static Serial &getInstance() {
        static Serial instance;
        return instance;
    }

    void initialize();

    void send(const std::span<uint8_t> &data);

    std::span<uint8_t> receive(std::span<uint8_t> buffer);

  private:
    Serial();
    ~Serial();

    Serial(const Serial &) = delete;
    Serial &operator=(const Serial &) = delete;

    struct SerialImpl;
    SerialImpl *impl_;

    bool initialized_ = false;
};

}  // namespace transport
}  // namespace network
}  // namespace emb
