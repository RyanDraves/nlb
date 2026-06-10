#include "emb/yaal/audio.hpp"

#include <algorithm>

#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/pio.h"

#include "emb/yaal/pico/pio/i2s.pio.h"

namespace emb {
namespace yaal {

namespace {

// 2 PIO cycles per bit, 32 bits per stereo frame
constexpr uint32_t kPioCyclesPerFrame = 64;

}  // namespace

struct AudioOut::AudioOutImpl {
    PIO pio;
    uint sm;
    uint offset;
    int dma_channel;
    uint32_t sample_rate;

    void set_sample_rate(uint32_t rate) {
        sample_rate = rate;
        float div = static_cast<float>(clock_get_hz(clk_sys)) /
                    static_cast<float>(rate * kPioCyclesPerFrame);
        pio_sm_set_clkdiv(pio, sm, div);
    }
};

AudioOut::AudioOut(uint8_t data_pin, uint8_t clock_pin_base,
                   uint32_t sample_rate)
    : impl_(new AudioOutImpl) {
    // The data and clock pins aren't necessarily contiguous; claim a state
    // machine able to reach the full pin range
    uint8_t gpio_base = std::min(data_pin, clock_pin_base);
    uint8_t gpio_count =
        std::max<uint8_t>(data_pin, clock_pin_base + 1) - gpio_base + 1;
    pio_claim_free_sm_and_add_program_for_gpio_range(
        &audio_i2s_program, &impl_->pio, &impl_->sm, &impl_->offset, gpio_base,
        gpio_count, true /* set_gpio_base */);

    audio_i2s_program_init(impl_->pio, impl_->sm, impl_->offset, data_pin,
                           clock_pin_base);
    impl_->set_sample_rate(sample_rate);

    // The DMA channel is paced by the PIO TX FIFO, and reads clips directly
    // from flash, one 32-bit stereo frame per transfer
    impl_->dma_channel = dma_claim_unused_channel(true /* required */);
    dma_channel_config config =
        dma_channel_get_default_config(impl_->dma_channel);
    channel_config_set_transfer_data_size(&config, DMA_SIZE_32);
    channel_config_set_read_increment(&config, true);
    channel_config_set_write_increment(&config, false);
    channel_config_set_dreq(
        &config, pio_get_dreq(impl_->pio, impl_->sm, true /* is_tx */));
    dma_channel_configure(impl_->dma_channel, &config,
                          &impl_->pio->txf[impl_->sm], nullptr, 0,
                          false /* trigger */);

    pio_sm_set_enabled(impl_->pio, impl_->sm, true);
}

AudioOut::~AudioOut() {
    stop();
    pio_sm_set_enabled(impl_->pio, impl_->sm, false);
    dma_channel_unclaim(impl_->dma_channel);
    delete impl_;
}

void AudioOut::play(const AudioClip &clip) {
    stop();

    if (clip.sample_rate != impl_->sample_rate) {
        impl_->set_sample_rate(clip.sample_rate);
    }

    dma_channel_set_read_addr(impl_->dma_channel, clip.samples,
                              false /* trigger */);
    dma_channel_set_trans_count(impl_->dma_channel, clip.num_frames,
                                true /* trigger */);
}

bool AudioOut::is_playing() const {
    return dma_channel_is_busy(impl_->dma_channel);
}

void AudioOut::stop() {
    // Any residual frames in the PIO FIFO (~8) drain in under a millisecond,
    // so there's no need to clear them
    dma_channel_abort(impl_->dma_channel);
}

}  // namespace yaal
}  // namespace emb
