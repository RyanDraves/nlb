#include <span>
#include <vector>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "emb/network/serialize/bh_cobs.hpp"
#include "emb/network/serialize/test_bh.hpp"

using namespace testing;

namespace emb {
namespace network {
namespace serialize {

TEST(BhCobsTest, TestBasic) {
    BhCobs serializer;

    testdata::Foo in_data{42, {1, 2, 3}, "hello"};

    std::vector<uint8_t> buffer;
    buffer.resize(1000);

    auto [serialized, frame_padding] = serializer.serialize(in_data, buffer);

    auto framed = serializer.frame(serialized);

    auto deframed = serializer.deframe(framed);

    testdata::Foo out_data = serializer.deserialize<testdata::Foo>(deframed);

    ASSERT_THAT(out_data.bar, Eq(in_data.bar));
    ASSERT_THAT(out_data.baz, Eq(in_data.baz));
    ASSERT_THAT(out_data.qux, Eq(in_data.qux));
}

}  // namespace serialize
}  // namespace network
}  // namespace emb
