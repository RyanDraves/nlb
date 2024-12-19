#pragma once

#include <cinttypes>
#include <span>

namespace emb {
namespace network {
namespace transport {

class Zmq {
  public:
    static Zmq &getInstance() {
        static Zmq instance;
        return instance;
    }

    void initialize();

    void send(const std::span<uint8_t> &data);

    std::span<uint8_t> receive(std::span<uint8_t> buffer);

  private:
    Zmq();
    ~Zmq();

    Zmq(const Zmq &) = delete;
    Zmq &operator=(const Zmq &) = delete;

    struct ZmqImpl;
    ZmqImpl *impl_;

    bool initialized_ = false;
};

}  // namespace transport
}  // namespace network
}  // namespace emb
