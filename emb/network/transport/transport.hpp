#pragma once

#include <cinttypes>
#include <span>

namespace emb {
namespace network {
namespace transport {

class Transport {
  public:
    Transport();
    ~Transport();

    void initialize();

    void send(const std::span<uint8_t> &data);

    std::span<uint8_t> receive(std::span<uint8_t> buffer);

  private:
    struct TransportImpl;
    TransportImpl *impl_;
};

}  // namespace transport
}  // namespace network
}  // namespace emb
