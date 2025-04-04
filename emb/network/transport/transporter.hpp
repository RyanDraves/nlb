#pragma once

#include <cinttypes>
#include <concepts>
#include <span>

namespace emb {
namespace network {
namespace transport {

// Concept for a transport layer
template <typename T>
concept TransporterLike = requires(T t, std::span<uint8_t> data) {
    { t.initialize() } -> std::same_as<void>;
    { t.send(data) } -> std::same_as<void>;
    { t.receive(data) } -> std::same_as<std::span<uint8_t>>;
    { t.getInstance() } -> std::same_as<T &>;
};

}  // namespace transport
}  // namespace network
}  // namespace emb
