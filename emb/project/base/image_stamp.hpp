#pragma once

#include <cinttypes>
#include <span>

namespace emb {
namespace project {
namespace base {

// A stamp embedded in the firmware image. The hash field is zero in the
// compiled binary and patched post-build with the SHA256 of the image
// (computed with the hash field zeroed) by
// `//emb/project/bootloader:stamp`, which locates the stamp by its magic.
struct ImageStamp {
    uint8_t magic[16];
    uint8_t hash[32];
};

// The SHA256 of the running image, as stamped into the binary
std::span<const uint8_t> image_hash();

}  // namespace base
}  // namespace project
}  // namespace emb
