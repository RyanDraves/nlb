#include <span>
#include <vector>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "emb/network/serialize/cbor2_cobs.hpp"

using namespace testing;

namespace emb {
namespace network {
namespace serialize {

namespace {
struct Foo {
    int id;
};
}  // namespace

TEST(Cbor2CobsTest, TestBasic) {
    Cbor2Cobs serializer;

    Foo in_data{42};

    std::vector<uint8_t> buffer;
    buffer.resize(1000);

    auto [serialized, frame_padding] = serializer.serialize(in_data, buffer);

    auto framed = serializer.frame(serialized);

    auto deframed = serializer.deframe(framed);

    Foo out_data = serializer.deserialize<Foo>(deframed);

    ASSERT_THAT(out_data.id, Eq(in_data.id));
}

}  // namespace serialize
}  // namespace network
}  // namespace emb
