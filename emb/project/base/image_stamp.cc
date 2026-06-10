#include "emb/project/base/image_stamp.hpp"

namespace emb {
namespace project {
namespace base {

namespace {

// Place the stamp in a dedicated section on device builds; host (Mach-O)
// builds reject ELF section names, and only device images get stamped.
#if defined(__arm__)
#define IMAGE_STAMP_SECTION __attribute__((used, section(".image_stamp")))
#else
#define IMAGE_STAMP_SECTION __attribute__((used))
#endif

// NOTE: The magic must match `MAGIC` in `emb/project/bootloader/stamp.py`
IMAGE_STAMP_SECTION const ImageStamp g_image_stamp = {
    .magic = {'N', 'L', 'B', '-', 'I', 'M', 'A', 'G', 'E', '-', 'S', 'T', 'A',
              'M', 'P', '!'},
    .hash = {},
};

}  // namespace

std::span<const uint8_t> image_hash() { return g_image_stamp.hash; }

}  // namespace base
}  // namespace project
}  // namespace emb
