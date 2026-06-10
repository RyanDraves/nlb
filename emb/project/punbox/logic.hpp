#pragma once

#include <cinttypes>

#include "emb/yaal/audio.hpp"
#include "emb/yaal/audio_clip.hpp"
#include "emb/yaal/gpio.hpp"

namespace emb {
namespace project {
namespace punbox {

// Core punbox behavior: a debounced, active-low button triggers clip playback
class PunboxLogic {
  public:
    static constexpr uint32_t kDebounceMs = 20;

    PunboxLogic(yaal::Gpio &button, yaal::AudioOut &audio,
                const yaal::AudioClip &clip);

    // Poll the button; call from the main loop.
    //
    // The first tick seeds the debounce state from the current level without
    // triggering, so a button held at boot doesn't fire a phantom press.
    void tick(uint32_t now_ms);

    // Start playback, as if the button were pressed
    void trigger();

    uint32_t press_count() const { return press_count_; }
    bool playing() const { return audio_.is_playing(); }

  private:
    yaal::Gpio &button_;
    yaal::AudioOut &audio_;
    const yaal::AudioClip &clip_;

    bool initialized_ = false;
    // Pulled-up levels; `false` is pressed
    bool stable_level_ = true;
    bool last_level_ = true;
    uint32_t last_change_ms_ = 0;
    uint32_t press_count_ = 0;
};

}  // namespace punbox
}  // namespace project
}  // namespace emb
