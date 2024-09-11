#include <iostream>
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

    // Print the buffer
    std::cout << "Serialized: ";
    for (size_t i = 0; i < serialized.size(); i++) {
        std::cout << std::hex << (int)serialized[i] << " ";
    }
    std::cout << std::endl;

    auto framed = serializer.frame(serialized);

    // Print the buffer
    std::cout << "Framed: ";
    for (size_t i = 0; i < framed.size(); i++) {
        std::cout << std::hex << (int)framed[i] << " ";
    }
    std::cout << std::endl;

    auto deframed = serializer.deframe(framed);

    // Print the buffer
    std::cout << "Deframed: ";
    for (size_t i = 0; i < deframed.size(); i++) {
        std::cout << std::hex << (int)deframed[i] << " ";
    }
    std::cout << std::endl;

    testdata::Foo out_data = serializer.deserialize<testdata::Foo>(deframed);

    // Print out_data
    std::cout << "Deserialized: " << out_data.bar << " " << out_data.baz << " ";
    for (size_t i = 0; i < out_data.qux.size(); i++) {
        std::cout << out_data.qux[i] << " ";
    }
    std::cout << std::endl;

    ASSERT_THAT(out_data.bar, Eq(in_data.bar));
    ASSERT_THAT(out_data.baz, Eq(in_data.baz));
    ASSERT_THAT(out_data.qux, Eq(in_data.qux));
}

}  // namespace serialize
}  // namespace network
}  // namespace emb
