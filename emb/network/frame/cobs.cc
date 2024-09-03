#include <cassert>
#include <cstddef>
#include <cstdint>

namespace emb {
namespace network {
namespace frame {

// Implementation borrowed from Wikipedia
// https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing

size_t cobsEncode(const uint8_t *data, size_t length, uint8_t const *buffer) {
    assert(data && buffer);

    uint8_t *encode = (uint8_t *)buffer;  // Encoded byte pointer
    uint8_t *codep = encode++;            // Output code pointer
    uint8_t code = 1;                     // Code value

    for (const uint8_t *byte = (const uint8_t *)data; length--; ++byte) {
        if (*byte)  // Byte not zero, write it
            *encode++ = *byte, ++code;

        if (!*byte ||
            code == 0xff)  // Input is zero or block completed, restart
        {
            *codep = code, code = 1, codep = encode;
            if (!*byte || length)
                ++encode;
        }
    }
    *codep = code;  // Write final code value

    return (size_t)(encode - buffer);
}

size_t cobsDecode(const uint8_t *buffer, size_t length, uint8_t const *data) {
    const uint8_t *byte = buffer;       // Encoded input byte pointer
    uint8_t *decode = (uint8_t *)data;  // Decoded output byte pointer

    for (uint8_t code = 0xff, block = 0; byte < buffer + length; --block) {
        if (block)  // Decode block byte
            *decode++ = *byte++;
        else {
            block = *byte++;  // Fetch the next block length
            if (block &&
                (code !=
                 0xff))  // Encoded zero, write it unless it's delimiter.
                *decode++ = 0;
            code = block;
            if (!code)  // Delimiter code found
                break;
        }
    }

    return (size_t)(decode - (uint8_t *)data);
}

}  // namespace frame
}  // namespace network
}  // namespace emb
