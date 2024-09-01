#pragma once

#include <concepts>
#include <inttypes.h>
#include <span>

namespace emb {
namespace network {
namespace serialize {

// Cheeky Python-like "Any" type;
// helps resolve template overloads
struct Any {};

template <typename T>
concept SerializerLike = requires(T t, std::span<uint8_t> buffer) {
    { t.frame(buffer) } -> std::same_as<std::span<uint8_t>>;
    { t.deframe(buffer) } -> std::same_as<std::span<uint8_t>>;
    {
        t.template serialize<Any>(Any{}, buffer)
    } -> std::same_as<std::pair<std::span<uint8_t>, size_t>>;
    { t.template deserialize<Any>(buffer) } -> std::same_as<Any>;
    { T::kMaxOverhead + 0 } -> std::same_as<size_t>;
    { T::kBufSize + 0 } -> std::same_as<size_t>;
};

}  // namespace serialize
}  // namespace network
}  // namespace emb
