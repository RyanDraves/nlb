#include "emb/network/transport/serial.hpp"

#include "zmq.hpp"
#include <vector>

namespace emb {
namespace network {
namespace transport {

// Our host "serial" implementation is a ZMQ socket;
// rather than making a `tcp` transporter, implementing the
// serial class lets us compile the same code on the host
// and set up simple client <-> host tests.
struct Serial::SerialImpl {
    zmq::context_t context;
    zmq::socket_t socket;

    SerialImpl() {}

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

Serial::Serial() : impl_(new SerialImpl) {}

Serial::~Serial() { delete impl_; }

void Serial::initialize() { impl_->initialize(); }

void Serial::send(const std::span<uint8_t> &data) { impl_->send(data); }

std::span<uint8_t> Serial::receive(std::span<uint8_t> buffer) {
    return impl_->receive(buffer);
}

}  // namespace transport
}  // namespace network
}  // namespace emb
