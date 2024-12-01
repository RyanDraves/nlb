#include "emb/network/transport/serial.hpp"
#include "emb/network/transport/transporter.hpp"

#include <vector>

namespace emb {
namespace network {
namespace transport {

struct Serial::SerialImpl {
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

Serial::Serial() : impl_(new SerialImpl) {}

Serial::~Serial() { delete impl_; }

void Serial::initialize() {}

void Serial::send(const std::span<uint8_t> &data) { impl_->send(data); }

std::span<uint8_t> Serial::receive(std::span<uint8_t> buffer) {
    return impl_->receive(buffer);
}

static_assert(TransporterLike<Serial>);

}  // namespace transport
}  // namespace network
}  // namespace emb
