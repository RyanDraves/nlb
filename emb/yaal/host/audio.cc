#include "emb/yaal/audio.hpp"

namespace emb {
namespace yaal {

struct AudioOut::AudioOutImpl {};

AudioOut::AudioOut(uint8_t data_pin, uint8_t clock_pin_base,
                   uint32_t sample_rate)
    : impl_(nullptr) {}

AudioOut::~AudioOut() {}

void AudioOut::play(const AudioClip &clip) { return; }

bool AudioOut::is_playing() const { return false; }

void AudioOut::stop() { return; }

}  // namespace yaal
}  // namespace emb
