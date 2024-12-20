#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "emb/util/ring_buffer.hpp"

using namespace testing;

namespace emb {
namespace util {

class RingBufferTest : public Test {
  protected:
    RingBuffer<int, 5> buffer;
    RingBuffer<int, 5> initialized_buffer{1, 2, 3, 4, 5};
};

TEST_F(RingBufferTest, IsEmptyInitially) {
    EXPECT_TRUE(buffer.empty());
    EXPECT_FALSE(buffer.full());
    EXPECT_FALSE(buffer.contains(0));
}

TEST_F(RingBufferTest, AddElement) {
    buffer.push(1);
    EXPECT_FALSE(buffer.empty());
    EXPECT_FALSE(buffer.full());
    EXPECT_EQ(buffer.size(), 1);
    EXPECT_TRUE(buffer.contains(1));
}

TEST_F(RingBufferTest, PopElement) {
    buffer.push(1);
    int value = buffer.pop();
    EXPECT_EQ(value, 1);
    EXPECT_TRUE(buffer.empty());
    EXPECT_FALSE(buffer.full());
    EXPECT_FALSE(buffer.contains(1));
}

TEST_F(RingBufferTest, FillBuffer) {
    for (int i = 0; i < 5; ++i) {
        buffer.push(i);
    }
    EXPECT_TRUE(buffer.full());
    EXPECT_FALSE(buffer.empty());
    EXPECT_EQ(buffer.size(), 5);
    EXPECT_TRUE(buffer.contains(0));
}

TEST_F(RingBufferTest, OverflowBuffer) {
    for (int i = 0; i < 5; ++i) {
        buffer.push(i);
    }
    buffer.push(5);
    EXPECT_TRUE(buffer.full());
    EXPECT_EQ(buffer.size(), 5);
    EXPECT_EQ(buffer.pop(), 1);  // Oldest element should be removed
    EXPECT_FALSE(buffer.contains(1));
    EXPECT_TRUE(buffer.contains(5));
}

TEST_F(RingBufferTest, InitializedBuffer) {
    EXPECT_FALSE(initialized_buffer.empty());
    EXPECT_TRUE(initialized_buffer.full());
    EXPECT_EQ(initialized_buffer.size(), 5);
    EXPECT_EQ(initialized_buffer.pop(), 1);
    EXPECT_EQ(initialized_buffer.size(), 4);
    EXPECT_TRUE(initialized_buffer.contains(2));
}

}  // namespace util
}  // namespace emb
