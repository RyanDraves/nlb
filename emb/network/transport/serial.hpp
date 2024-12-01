#pragma once

#include <cinttypes>
#include <span>
#include <stdio.h>

namespace emb {
namespace network {
namespace transport {

class Serial {
  public:
    Serial();
    ~Serial();

    void initialize();

    void send(const std::span<uint8_t> &data);

    std::span<uint8_t> receive(std::span<uint8_t> buffer);

  private:
    struct SerialImpl;
    SerialImpl *impl_;
};

}  // namespace transport
}  // namespace network
}  // namespace emb
