#include <span>

#include "zmq.hpp"
#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "emb/network/transport/transport.hpp"

using namespace testing;

namespace emb {
namespace network {
namespace transport {

TEST(ZmqTest, TestBasic) {
    // Create a simple ZMQ client and connnect to the unittest port
    zmq::context_t context(1);
    zmq::socket_t client(context, zmq::socket_type::dealer);
    client.connect("ipc://unittest");

    Transport transport;
    transport.initialize();
    std::vector<uint8_t> data = {0x01, 0x02, 0x03, 0x04};

    // Send the data
    client.send(zmq::buffer(data), zmq::send_flags::none);
    std::vector<uint8_t> buffer(data.size());
    auto resp = transport.receive(std::span<uint8_t>(buffer));

    // Server-side validation
    ASSERT_THAT(resp.size(), Eq(data.size()));
    ASSERT_THAT(resp, ElementsAreArray(data));

    // Receive the data
    transport.send(std::span<uint8_t>(data));
    zmq::message_t message;
    auto resp2 = client.recv(message, zmq::recv_flags::none);

    // Client-side validation
    ASSERT_THAT(resp2.has_value(), Eq(true));
    ASSERT_THAT(message.size(), Eq(data.size()));
    ASSERT_THAT(std::memcmp(message.data(), data.data(), data.size()), Eq(0));
}

}  // namespace transport
}  // namespace network
}  // namespace emb
