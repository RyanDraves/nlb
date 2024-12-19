#include "emb/network/transport/zmq.hpp"

#include "zmq.hpp"
#include <vector>

namespace emb {
namespace network {
namespace transport {

struct Zmq::ZmqImpl {
    zmq::context_t context;
    zmq::socket_t socket;

    ZmqImpl() {}

    void initialize() {

        // Create a ZMQ context
        context = zmq::context_t(1);

        // Check if the UNITTEST envvar is set
        if (std::getenv("UNITTEST")) {
            socket = zmq::socket_t(context, zmq::socket_type::dealer);
            // Bind the socket to an inproc address
            socket.bind("ipc://unittest");
        } else {
            socket = zmq::socket_t(context, zmq::socket_type::dealer);
            // Bind the socket to a TCP port
            socket.bind("tcp://*:1337");
        }
    }

    void send(const std::span<uint8_t> &data) {
        // Send the message
        socket.send(zmq::buffer(data.data(), data.size()),
                    zmq::send_flags::none);
    }

    std::span<uint8_t> receive(std::span<uint8_t> buffer) {
        auto result = socket.recv(zmq::buffer(buffer.data(), buffer.size()),
                                  zmq::recv_flags::none);

        if (!result.has_value()) {
            return {};
        }

        // Note: if .size != .untruncated_size, our buffer was too small.
        // Let's assume for now that the buffer is large enough.
        return buffer.subspan(0, result.value().size);
    }
};

Zmq::Zmq() : impl_(new ZmqImpl) {}

Zmq::~Zmq() { delete impl_; }

void Zmq::initialize() {
    if (initialized_) {
        return;
    }
    impl_->initialize();
    initialized_ = true;
}

void Zmq::send(const std::span<uint8_t> &data) { impl_->send(data); }

std::span<uint8_t> Zmq::receive(std::span<uint8_t> buffer) {
    return impl_->receive(buffer);
}

}  // namespace transport
}  // namespace network
}  // namespace emb
