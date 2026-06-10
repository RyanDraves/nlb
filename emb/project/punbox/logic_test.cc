#include "emb/project/punbox/logic.hpp"

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "emb/yaal/audio_clip.hpp"
#include "emb/yaal/host/audio.hpp"
#include "emb/yaal/host/gpio.hpp"

using namespace testing;

namespace emb {
namespace project {
namespace punbox {

namespace {

constexpr int16_t kSamples[] = {0, 0, 100, 100};
constexpr yaal::AudioClip kClip{
    .sample_rate = 22050,
    .num_frames = 2,
    .samples = kSamples,
};

constexpr uint32_t kDebounce = PunboxLogic::kDebounceMs;

}  // namespace

class PunboxLogicTest : public Test {
  protected:
    PunboxLogicTest() : button_(0), logic_(button_, audio_, kClip) {
        // Seed the debounce state with the button released
        button_.set_level(true);
        logic_.tick(0);
    }

    yaal::host::HostGpio button_;
    yaal::host::HostAudioOut audio_;
    PunboxLogic logic_;
};

TEST_F(PunboxLogicTest, PressPlaysClipOnce) {
    button_.set_level(false);
    logic_.tick(10);
    // Not yet debounced
    EXPECT_EQ(audio_.played_clips().size(), 0);
    EXPECT_EQ(logic_.press_count(), 0);

    logic_.tick(10 + kDebounce);
    ASSERT_EQ(audio_.played_clips().size(), 1);
    EXPECT_EQ(audio_.played_clips()[0], &kClip);
    EXPECT_EQ(logic_.press_count(), 1);
    EXPECT_TRUE(logic_.playing());
}

TEST_F(PunboxLogicTest, HoldPlaysOnce) {
    button_.set_level(false);
    logic_.tick(10);
    logic_.tick(10 + kDebounce);
    EXPECT_EQ(logic_.press_count(), 1);

    // Holding the button doesn't retrigger
    logic_.tick(10 + 10 * kDebounce);
    logic_.tick(10 + 20 * kDebounce);
    EXPECT_EQ(audio_.played_clips().size(), 1);
    EXPECT_EQ(logic_.press_count(), 1);
}

TEST_F(PunboxLogicTest, BounceWithinWindowPlaysOnce) {
    // The contact bounces every few milliseconds before settling
    button_.set_level(false);
    logic_.tick(10);
    button_.set_level(true);
    logic_.tick(13);
    button_.set_level(false);
    logic_.tick(16);
    EXPECT_EQ(audio_.played_clips().size(), 0);

    // Stable for a full debounce window after the last bounce
    logic_.tick(16 + kDebounce);
    EXPECT_EQ(audio_.played_clips().size(), 1);
    EXPECT_EQ(logic_.press_count(), 1);
}

TEST_F(PunboxLogicTest, ReleaseAndRepressRetriggers) {
    button_.set_level(false);
    logic_.tick(10);
    logic_.tick(10 + kDebounce);
    EXPECT_EQ(logic_.press_count(), 1);

    button_.set_level(true);
    logic_.tick(100);
    logic_.tick(100 + kDebounce);
    EXPECT_EQ(logic_.press_count(), 1);

    button_.set_level(false);
    logic_.tick(200);
    logic_.tick(200 + kDebounce);
    EXPECT_EQ(audio_.played_clips().size(), 2);
    EXPECT_EQ(logic_.press_count(), 2);
}

TEST_F(PunboxLogicTest, ReleaseDoesNotPlay) {
    button_.set_level(false);
    logic_.tick(10);
    logic_.tick(10 + kDebounce);

    button_.set_level(true);
    logic_.tick(100);
    logic_.tick(100 + kDebounce);
    // Only the press played, not the release
    EXPECT_EQ(audio_.played_clips().size(), 1);
}

TEST_F(PunboxLogicTest, TriggerPlaysAndCounts) {
    logic_.trigger();
    ASSERT_EQ(audio_.played_clips().size(), 1);
    EXPECT_EQ(audio_.played_clips()[0], &kClip);
    EXPECT_EQ(logic_.press_count(), 1);
}

TEST(PunboxLogicSeedTest, ButtonHeldAtBootDoesNotPlay) {
    yaal::host::HostGpio button(0);
    yaal::host::HostAudioOut audio;
    PunboxLogic logic(button, audio, kClip);

    // Held (or, on the host platform, constantly low) from the first tick
    button.set_level(false);
    logic.tick(0);
    logic.tick(kDebounce);
    logic.tick(10 * kDebounce);
    EXPECT_EQ(audio.played_clips().size(), 0);
    EXPECT_EQ(logic.press_count(), 0);

    // A release and fresh press still triggers
    button.set_level(true);
    logic.tick(1000);
    logic.tick(1000 + kDebounce);
    button.set_level(false);
    logic.tick(2000);
    logic.tick(2000 + kDebounce);
    EXPECT_EQ(audio.played_clips().size(), 1);
    EXPECT_EQ(logic.press_count(), 1);
}

}  // namespace punbox
}  // namespace project
}  // namespace emb
