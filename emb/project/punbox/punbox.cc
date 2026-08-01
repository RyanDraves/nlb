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

struct Punbox::PunboxImpl {
    // Pin constants come from `punbox.bh`, shared with the hardware design
    PunboxImpl()
        : button(kButtonPin),
          audio(kI2SDataPin, kI2SClockPinBase, rimshot.sample_rate),
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
