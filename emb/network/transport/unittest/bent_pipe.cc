#include "emb/network/transport/transport.hpp"
#include "emb/network/transport/transporter.hpp"

#include <vector>

namespace emb {
namespace network {
namespace transport {

// Simple bent-pipe implementation for unit tests

struct Transport::TransportImpl {
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

Transport::Transport() : impl_(new TransportImpl) {}

Transport::~Transport() { delete impl_; }

void Transport::initialize() {}

void Transport::send(const std::span<uint8_t> &data) { impl_->send(data); }

std::span<uint8_t> Transport::receive(std::span<uint8_t> buffer) {
    return impl_->receive(buffer);
}

static_assert(TransporterLike<Transport>);

}  // namespace transport
}  // namespace network
}  // namespace emb
