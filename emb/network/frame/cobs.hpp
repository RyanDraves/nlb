#pragma once

#include <cassert>
#include <cstddef>
#include <cstdint>

namespace emb {
namespace network {
namespace frame {

/** COBS encode data to buffer
        @param data Pointer to input data to encode
        @param length Number of bytes to encode
        @param buffer Pointer to encoded output buffer
        @return Encoded buffer length in bytes
        @note Does not output delimiter byte
*/
size_t cobsEncode(const uint8_t *data, size_t length, uint8_t const *buffer);

/** COBS decode data from buffer
        @param buffer Pointer to encoded input bytes
        @param length Number of bytes to decode
        @param data Pointer to decoded output data
        @return Number of bytes successfully decoded
        @note Stops decoding if delimiter byte is found
*/
size_t cobsDecode(const uint8_t *buffer, size_t length, uint8_t const *data);

}  // namespace frame
}  // namespace network
}  // namespace emb
