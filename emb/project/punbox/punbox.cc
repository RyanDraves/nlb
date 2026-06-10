#include <cinttypes>

#include "emb/project/base/base_bh.hpp"
#include "emb/project/punbox/punbox_bh.hpp"

#include "emb/project/punbox/logic.hpp"
#include "emb/project/punbox/rimshot.hpp"
#include "emb/yaal/audio.hpp"
#include "emb/yaal/gpio.hpp"
#include "emb/yaal/timer.hpp"

namespace emb {
namespace project {
namespace punbox {

namespace {

// I2S pinout for the Waveshare Pico-Audio (original revision)
constexpr uint8_t kI2sDataPin = 26;       // DIN
constexpr uint8_t kI2sClockPinBase = 27;  // BCK, with LRCK on 28
constexpr uint8_t kButtonPin = 6;         // Active-low, against an internal pull-up

}  // namespace

struct Punbox::PunboxImpl {
    PunboxImpl()
        : button(kButtonPin),
          audio(kI2sDataPin, kI2sClockPinBase, rimshot.sample_rate),
          logic(button, audio, rimshot) {}

    void initialize() { button.set_mode(yaal::Mode::INPUT_PULLUP); }

    PunboxState state() const {
        PunboxState s;
        s.press_count = logic.press_count();
        s.playing = logic.playing();
        return s;
    }

    yaal::Gpio button;
    yaal::AudioOut audio;
    PunboxLogic logic;
};

Punbox::Punbox() : impl_(new PunboxImpl) {}

Punbox::~Punbox() { delete impl_; }

void Punbox::initialize() { impl_->initialize(); }

PunboxState Punbox::play_sound(const base::Ping &ping) {
    impl_->logic.trigger();
    return impl_->state();
}

PunboxState Punbox::get_state(const base::Ping &ping) {
    return impl_->state();
}

void Punbox::tick() { impl_->logic.tick(yaal::get_time_ms()); }

}  // namespace punbox
}  // namespace project
}  // namespace emb
