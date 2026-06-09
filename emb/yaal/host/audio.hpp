#include "emb/yaal/audio.hpp"

#include <vector>

namespace emb {
namespace yaal {
namespace host {

class HostAudioOut : public AudioOut {
  public:
    HostAudioOut() : AudioOut(0 /* data */, 1 /* clocks */, 22050) {}

    void play(const AudioClip &clip) override {
        played_clips_.push_back(&clip);
        playing_ = true;
    }

    bool is_playing() const override { return playing_; }

    void stop() override { playing_ = false; }

    // Simulate playback completing
    void set_playing(bool playing) { playing_ = playing; }

    const std::vector<const AudioClip *> &played_clips() const {
        return played_clips_;
    }

  private:
    std::vector<const AudioClip *> played_clips_;
    bool playing_ = false;
};

}  // namespace host
}  // namespace yaal
}  // namespace emb
