#include <span>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "emb/slic/hc_sr04.hpp"
#include "emb/yaal/host/gpio.hpp"

using namespace testing;

namespace emb {
namespace slic {

TEST(HcSr04Test, TestHcSr04) {
    // Test the HcSr04 class
    yaal::host::HostGpio trigger(0);
    yaal::host::HostGpio echo(1);
    HcSr04 hc_sr04(trigger, echo);

    // Echo pin never goes high
    echo.set_level(false);
    EXPECT_EQ(hc_sr04.get_distance_mm(), 0);

    // Echo pin never goes low (max distance)
    echo.set_level(true);
    EXPECT_EQ(hc_sr04.get_distance_mm(), 4000);
}

}  // namespace slic
}  // namespace emb
