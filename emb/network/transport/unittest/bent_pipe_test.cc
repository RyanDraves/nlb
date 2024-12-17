#include <span>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "emb/network/transport/transport.hpp"

using namespace testing;

namespace emb {
namespace network {
namespace transport {

TEST(BentPipeTest, TestBasic) {
    Transport transport;
    std::vector<uint8_t> data = {0x01, 0x02, 0x03, 0x04};
    transport.send(data);

    std::vector<uint8_t> buffer(data.size());
    std::span<uint8_t> received = transport.receive(buffer);

    ASSERT_THAT(received.size(), Eq(buffer.size()));
    ASSERT_THAT(received, ElementsAreArray(data));
}

}  // namespace transport
}  // namespace network
}  // namespace emb
