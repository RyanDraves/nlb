#include <span>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "emb/slic/hc_sr04.hpp"

using namespace testing;

namespace emb {
namespace slic {

TEST(HcSr04Test, TestHcSr04) {
    // Test the HcSr04 class
    yaal::Gpio trigger(0);
    yaal::Gpio echo(1);
    HcSr04 hc_sr04(trigger, echo);

    // TODO: Clever mocking for a real test

    // Test the get_distance_mm method
    EXPECT_EQ(hc_sr04.get_distance_mm(), 0);
}

}  // namespace slic
}  // namespace emb
