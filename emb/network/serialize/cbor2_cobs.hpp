#pragma once

#include <inttypes.h>
#include <span>

#include "cbor.h"
#include "rfl/Processors.hpp"
#include "rfl/cbor/Parser.hpp"
#include "rfl/cbor/read.hpp"
#include "rfl/cbor/write.hpp"

#include "emb/network/frame/cobs.hpp"

namespace emb {
namespace network {
namespace serialize {

namespace {
template <class... Ps>
void write_into_buffer(const auto &_obj, CborEncoder *_encoder,
                       std::span<uint8_t> _buffer) noexcept {
    using T = std::remove_cvref_t<decltype(_obj)>;
    using ParentType = rfl::parsing::Parent<rfl::cbor::Writer>;
    cbor_encoder_init(_encoder, _buffer.data(), _buffer.size(), 0);
    const auto writer = rfl::cbor::Writer(_encoder);
    rfl::cbor::Parser<T, rfl::Processors<Ps...>>::write(
        writer, _obj, typename ParentType::Root{});
}

// Custom CBOR write function to use std::span;
// borrows heavily from rfl/cbor/write.hpp
template <class... Ps>
size_t write(const auto &_obj, std::span<uint8_t> buffer) noexcept {
    CborEncoder encoder;
    write_into_buffer<Ps...>(_obj, &encoder, buffer);
    // Trust our buffer is large enough; skip
    // `cbor_encoder_get_extra_bytes_needed`
    const auto length = cbor_encoder_get_buffer_size(&encoder, buffer.data());
    return length;
}
}  // namespace

class Cbor2Cobs {
  public:
    constexpr static size_t kBufSize = 1024;
    constexpr static size_t kMaxOverhead = 1 + (kBufSize / 0xFE);

    Cbor2Cobs();
    ~Cbor2Cobs();

    std::span<uint8_t> frame(std::span<uint8_t> buffer) {
        // COBS encode the message
        size_t cobs_size = emb::network::frame::cobsEncode(
            buffer.data() + kMaxOverhead, buffer.size() - kMaxOverhead,
            buffer.data());
        // Make sure the message is null-terminated
        buffer[cobs_size] = 0;
        return buffer.subspan(0, cobs_size + 1);
    }

    template <typename M>
    std::pair<std::span<uint8_t>, size_t> serialize(const M &message,
                                                    std::span<uint8_t> buffer) {
        size_t msg_size =
            write(message,
                  buffer.subspan(kMaxOverhead, buffer.size() - kMaxOverhead));

        return std::make_pair(buffer.subspan(0, kMaxOverhead + msg_size),
                              kMaxOverhead);
    }

    std::span<uint8_t> deframe(std::span<uint8_t> buffer) {
        // Decode in place
        size_t msg_size = emb::network::frame::cobsDecode(
            buffer.data(), buffer.size(), buffer.data());
        return buffer.subspan(0, msg_size);
    }

    template <typename M> M deserialize(std::span<uint8_t> buffer) {
        return rfl::cbor::read<M>(reinterpret_cast<char *>(buffer.data()),
                                  buffer.size())
            .value();
    }
};

}  // namespace serialize
}  // namespace network
}  // namespace emb
