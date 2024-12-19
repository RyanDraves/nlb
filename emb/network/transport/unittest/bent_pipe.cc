#include "emb/network/transport/bent_pipe.hpp"
#include "emb/network/transport/transporter.hpp"

#include <vector>

namespace emb {
namespace network {
namespace transport {

// Simple bent-pipe implementation for unit tests

struct BentPipe::BentPipeImpl {
    std::vector<uint8_t> buffer_;

    void send(const std::span<uint8_t> &data) {
        buffer_.clear();
        buffer_.insert(buffer_.end(), data.begin(), data.end());
    }

    std::span<uint8_t> receive(std::span<uint8_t> buffer) {
        // Copy the buffer into the receive buffer
        for (size_t i = 0; i < buffer_.size(); i++) {
            buffer[i] = buffer_[i];
        }

        return buffer.subspan(0, buffer_.size());
    }
};

BentPipe::BentPipe() : impl_(new BentPipeImpl) {}

BentPipe::~BentPipe() { delete impl_; }

void BentPipe::initialize() {
    if (initialized_) {
        return;
    }

    initialized_ = true;
}

void BentPipe::send(const std::span<uint8_t> &data) { impl_->send(data); }

std::span<uint8_t> BentPipe::receive(std::span<uint8_t> buffer) {
    return impl_->receive(buffer);
}

static_assert(TransporterLike<BentPipe>);

}  // namespace transport
}  // namespace network
}  // namespace emb
