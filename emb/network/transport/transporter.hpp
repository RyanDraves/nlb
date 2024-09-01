#pragma once

#include <concepts>
#include <inttypes.h>
#include <span>

namespace emb {
namespace network {
namespace transport {

// Concept for a transport layer
template <typename T>
concept TransporterLike = requires(T t, std::span<uint8_t> data) {
    { t.send(data) } -> std::same_as<void>;
    { t.receive(data) } -> std::same_as<std::span<uint8_t>>;
};

}  // namespace transport
}  // namespace network
}  // namespace emb
