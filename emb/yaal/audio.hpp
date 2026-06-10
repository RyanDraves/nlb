#pragma once

#include <cinttypes>

#include "emb/yaal/audio_clip.hpp"

namespace emb {
namespace yaal {

// Fire-and-forget I2S audio output.
//
// On the Pico, clips are streamed straight from flash to a PIO I2S program by
// DMA, so playback costs no CPU time. The host implementation is a no-op; see
// `host/audio.hpp` for a test double.
class AudioOut {
  public:
    // `data_pin` carries I2S DIN; `clock_pin_base` carries BCK with LRCK on
    // `clock_pin_base + 1`. `sample_rate` is the default rate, in Hz, used to
    // clock the I2S bus; it's updated per-clip on `play`.
    AudioOut(uint8_t data_pin, uint8_t clock_pin_base, uint32_t sample_rate);
    virtual ~AudioOut();

    // Begin playback of the clip, interrupting any current playback
    virtual void play(const AudioClip &clip);

    virtual bool is_playing() const;

    virtual void stop();

  private:
    struct AudioOutImpl;
    AudioOutImpl *impl_;
};

}  // namespace yaal
}  // namespace emb
