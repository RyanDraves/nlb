#pragma once

#include <cinttypes>
#include <span>

namespace emb {
namespace network {
namespace transport {

class BentPipe {
  public:
    static BentPipe &getInstance() {
        static BentPipe instance;
        return instance;
    }

    void initialize();

    void send(const std::span<uint8_t> &data);

    std::span<uint8_t> receive(std::span<uint8_t> buffer);

  private:
    BentPipe();
    ~BentPipe();

    BentPipe(const BentPipe &) = delete;
    BentPipe &operator=(const BentPipe &) = delete;

    struct BentPipeImpl;
    BentPipeImpl *impl_;

    bool initialized_ = false;
};

}  // namespace transport
}  // namespace network
}  // namespace emb
