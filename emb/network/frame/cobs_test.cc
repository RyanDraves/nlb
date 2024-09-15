#include <span>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "emb/network/frame/cobs.hpp"

using namespace testing;

namespace emb {
namespace network {
namespace frame {

// Test the cobsEncode function
TEST(CobsTest, TestCobsEncode) {
    // Simple tests provided in `cobs_test.py`

    // Test corner cases on block size
    uint8_t block_input0[0xFE];
    for (size_t i = 0; i < sizeof(block_input0); i++) {
        block_input0[i] = i + 1;
    }
    uint8_t block_output0[0xFF]{};
    uint8_t expected_block_output0[0xFF] = {0xFF};
    for (size_t i = 1; i < sizeof(expected_block_output0); i++) {
        expected_block_output0[i] = i;
    }
    size_t block_encodedLength0 =
        cobsEncode(block_input0, sizeof(block_input0), block_output0);
    // Check the encoded length and match it against the expected output
    ASSERT_THAT(block_encodedLength0, Eq(sizeof(expected_block_output0)));
    ASSERT_THAT(block_output0, ElementsAreArray(expected_block_output0));

    // Check that the input buffer can be the output buffer,
    // provided that the input buffer is sufficiently offset
    const uint8_t offset = 1;
    uint8_t block_input1[0xFE + offset];
    for (size_t i = 0; i < sizeof(block_input1) - offset; i++) {
        block_input1[i + offset] = i + 1;
    }
    size_t block_encodedLength1 = cobsEncode(
        block_input1 + offset, sizeof(block_input1) - offset, block_input1);
    // Check the encoded length and match it against the expected output
    ASSERT_THAT(block_encodedLength1, Eq(sizeof(expected_block_output0)));
    ASSERT_THAT(block_input1, ElementsAreArray(expected_block_output0));
}

// Test the cobsDecode function
TEST(CobsTest, TestCobsDecode) {
    // Simple tests provided in `cobs_test.py`

    const uint8_t input2[] = {0x02, 0x11, 0x02, 0x33, 0x02, 0x44};
    uint8_t output2[5]{};
    uint8_t expected_output2[] = {0x11, 0x00, 0x33, 0x00, 0x44};
    size_t decodedLength2 = cobsDecode(input2, sizeof(input2), output2);
    // Check the decoded length and match it against the expected output
    ASSERT_THAT(decodedLength2, Eq(sizeof(expected_output2)));
    ASSERT_THAT(output2, ElementsAreArray(expected_output2));

    // Check that the input buffer can be the output buffer,
    // provided that the input buffer is sufficiently offset
    uint8_t offset = 0;
    uint8_t input3[] = {0x02, 0x11, 0x02, 0x33, 0x02, 0x44};
    uint8_t expected_output3[] = {0x11, 0x00, 0x33, 0x00, 0x44};
    size_t decodedLength3 =
        cobsDecode(input3 + offset, sizeof(input3) - offset, input3);
    // Check the encoded length and match it against the expected output
    ASSERT_THAT(decodedLength3, Eq(sizeof(expected_output3)));
    auto input3_span = std::span{input3, sizeof(expected_output3)};
    ASSERT_THAT(input3_span, ElementsAreArray(expected_output3));

    // Test a large buffer
    uint8_t input4[0xFF * 2 + 3 + offset];
    for (size_t i = 0; i < sizeof(input4); i++) {
        input4[i] = 1;
    }
    input4[offset + 0] = 0xFF;
    input4[offset + 0xFF] = 0xFF;
    input4[offset + 0xFF * 2] = 0x3;
    uint8_t expected_output4[0xFF * 2]{};
    for (size_t i = 0; i < sizeof(expected_output4); i++) {
        expected_output4[i] = 1;
    }
    size_t decodedLength4 =
        cobsDecode(input4 + offset, sizeof(input4) - offset, input4);
    // Check the encoded length and match it against the expected output
    ASSERT_THAT(decodedLength4, Eq(sizeof(expected_output4)));
    auto input4_span = std::span{input4, sizeof(expected_output4)};
    ASSERT_THAT(input4_span, ElementsAreArray(expected_output4));
}

}  // namespace frame
}  // namespace network
}  // namespace emb
