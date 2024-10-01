#include <span>
#include <vector>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "emb/network/serialize/bh_cobs.hpp"
#include "emb/network/serialize/testdata/test_bh.hpp"

using namespace testing;

namespace emb {
namespace network {
namespace serialize {

TEST(BhCobsTest, TestBasic) {
    BhCobs serializer;

    std::vector<uint8_t> buffer;
    buffer.resize(1000);

    testdata::Foo in_data{42, "hello", {1, 2, 3}};

    auto [serialized, frame_padding] = serializer.serialize(in_data, buffer);
    auto framed = serializer.frame(serialized);
    auto deframed = serializer.deframe(framed);
    testdata::Foo out_data = serializer.deserialize<testdata::Foo>(deframed);

    ASSERT_THAT(out_data.bar, Eq(in_data.bar));
    ASSERT_THAT(out_data.baz, Eq(in_data.baz));
    ASSERT_THAT(out_data.qux, Eq(in_data.qux));

    testdata::Unaligned in_data_unaligned{.a = 255,
                                          .b = 65535,
                                          .c = -100000,
                                          .d = 100000,
                                          .e = "world",
                                          .f = {-12, -34, -56},
                                          .g = {7, 8, 9, 10},
                                          .h = {12, 13},
                                          .i = {14}};

    auto [serialized_unaligned, frame_padding_unaligned] =
        serializer.serialize(in_data_unaligned, buffer);
    auto framed_unaligned = serializer.frame(serialized_unaligned);
    auto deframed_unaligned = serializer.deframe(framed_unaligned);
    testdata::Unaligned out_data_unaligned =
        serializer.deserialize<testdata::Unaligned>(deframed_unaligned);

    ASSERT_THAT(out_data_unaligned.a, Eq(in_data_unaligned.a));
    ASSERT_THAT(out_data_unaligned.b, Eq(in_data_unaligned.b));
    ASSERT_THAT(out_data_unaligned.c, Eq(in_data_unaligned.c));
    ASSERT_THAT(out_data_unaligned.d, Eq(in_data_unaligned.d));
    ASSERT_THAT(out_data_unaligned.e, Eq(in_data_unaligned.e));
    ASSERT_THAT(out_data_unaligned.f, Eq(in_data_unaligned.f));
    ASSERT_THAT(out_data_unaligned.g, Eq(in_data_unaligned.g));
    ASSERT_THAT(out_data_unaligned.h, Eq(in_data_unaligned.h));
    ASSERT_THAT(out_data_unaligned.i, Eq(in_data_unaligned.i));

    testdata::Foo in_large_data{
        1,
        "hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh"
        "hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh"
        "hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh"
        "hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh",
        {
            1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2,
            3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
            1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2,
            3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
            1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2,
            3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
            1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2,
            3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
            1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2,
            3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
            1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2,
            3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
        }};

    auto [serialized_large, frame_padding_large] =
        serializer.serialize(in_large_data, buffer);
    auto framed_large = serializer.frame(serialized_large);
    auto deframed_large = serializer.deframe(framed_large);
    testdata::Foo out_large_data =
        serializer.deserialize<testdata::Foo>(deframed_large);

    ASSERT_THAT(out_large_data.bar, Eq(in_large_data.bar));
    ASSERT_THAT(out_large_data.baz, Eq(in_large_data.baz));
    ASSERT_THAT(out_large_data.qux, Eq(in_large_data.qux));
}

}  // namespace serialize
}  // namespace network
}  // namespace emb
