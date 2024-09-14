#pragma once

#include <inttypes.h>
#include <span>

#include "emb/network/frame/cobs.hpp"

namespace emb {
namespace network {
namespace serialize {

class BhCobs {
  public:
    constexpr static size_t kBufSize = 1024;
    constexpr static size_t kMaxOverhead = 1 + (kBufSize / 0xFE);

    BhCobs();
    ~BhCobs();

    std::span<uint8_t> frame(std::span<uint8_t> buffer) {
        // COBS encode the message
        size_t cobs_size = emb::network::frame::cobsEncode(
            buffer.data() + kMaxOverhead, buffer.size() - kMaxOverhead,
            buffer.data());
        // Make sure the message is null-terminated
        buffer[cobs_size] = 0;
        return buffer.subspan(0, cobs_size + 1);
    }

    template <class M>
    std::pair<std::span<uint8_t>, size_t> serialize(const M &message,
                                                    std::span<uint8_t> buffer) {
        auto msg_buffer = message.serialize(
            buffer.subspan(kMaxOverhead, buffer.size() - kMaxOverhead));

        return std::make_pair(
            buffer.subspan(0, kMaxOverhead + msg_buffer.size()), kMaxOverhead);
    }

    std::span<uint8_t> deframe(std::span<uint8_t> buffer) {
        // Decode in place
        size_t msg_size = emb::network::frame::cobsDecode(
            buffer.data(), buffer.size(), buffer.data());
        return buffer.subspan(0, msg_size);
    }

    template <class M> M deserialize(std::span<uint8_t> buffer) {
        return M::deserialize(buffer);
    }
};

}  // namespace serialize
}  // namespace network
}  // namespace emb
