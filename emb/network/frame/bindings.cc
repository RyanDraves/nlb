#include "emb/network/frame/cobs.hpp"
#include <pybind11/pybind11.h>

#include <string>

namespace py = pybind11;

namespace emb {
namespace network {
namespace frame {

PYBIND11_MODULE(cobs, m) {
    m.doc() = "emb COBS bindings";
    m.def(
        "cobs_encode",
        [](py::bytes *data) {
            // Wrap cobsEncode as def cobsEncode(data: bytes) -> bytes:

            // Hoppity skoppity this is now my property
            uint8_t *data_ptr;
            ssize_t length;
            PYBIND11_BYTES_AS_STRING_AND_SIZE(
                data->ptr(), reinterpret_cast<char **>(&data_ptr), &length);

            // Create our return buffer
            std::string buffer;
            // Worst-case overhead of one byte in 254, rounded up
            buffer.resize(length + 1 + (length / 0xFE));

            // Encode the data
            size_t encoded_size =
                cobsEncode(data_ptr, length,
                           reinterpret_cast<uint8_t const *>(buffer.data()));

            return py::bytes(buffer.c_str(), encoded_size);
        },
        py::arg("data"), "A function which encodes data using COBS");
    m.def(
        "cobs_decode",
        [](py::bytes *buffer) {
            // Wrap cobsDecode as def cobsDecode(buffer: bytes) -> bytes:

            // Hoppity skoppity this is now my property
            uint8_t *buffer_ptr;
            ssize_t length;
            PYBIND11_BYTES_AS_STRING_AND_SIZE(
                buffer->ptr(), reinterpret_cast<char **>(&buffer_ptr), &length);

            // Create our return buffer
            std::string data;
            // Best cast overhead is one byte
            data.resize(length - 1);

            // Decode the buffer
            size_t decoded_size =
                cobsDecode(buffer_ptr, length,
                           reinterpret_cast<uint8_t const *>(data.data()));

            return py::bytes(data.c_str(), decoded_size);
        },
        py::arg("buffer"), "A function which decodes a buffer using COBS");
}

}  // namespace frame
}  // namespace network
}  // namespace emb
