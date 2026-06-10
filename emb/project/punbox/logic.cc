#include "emb/project/punbox/logic.hpp"

namespace emb {
namespace project {
namespace punbox {

PunboxLogic::PunboxLogic(yaal::Gpio &button, yaal::AudioOut &audio,
                         const yaal::AudioClip &clip)
    : button_(button), audio_(audio), clip_(clip) {}

void PunboxLogic::tick(uint32_t now_ms) {
    bool level = button_.read();

    if (!initialized_) {
        initialized_ = true;
        stable_level_ = level;
        last_level_ = level;
        last_change_ms_ = now_ms;
        return;
    }

    if (level != last_level_) {
        // Level changed; restart the debounce window
        last_level_ = level;
        last_change_ms_ = now_ms;
    }

    if (level != stable_level_ && now_ms - last_change_ms_ >= kDebounceMs) {
        stable_level_ = level;
        if (!stable_level_) {
            // Falling edge: the button was pressed
            trigger();
        }
    }
}

void PunboxLogic::trigger() {
    audio_.play(clip_);
    ++press_count_;
}

}  // namespace punbox
}  // namespace project
}  // namespace emb
