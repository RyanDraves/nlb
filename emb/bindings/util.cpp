#include <pybind11/pybind11.h>
#include "emb/util/cobs.hpp"

#include <string>

namespace py = pybind11;

PYBIND11_MODULE(util, m)
{
  m.doc() = "emb util bindings";
  m.def("cobsEncode", [](py::bytes* data) {
    // Wrap cobsEncode as def cobsEncode(data: bytes) -> bytes:

    // Hoppity skoppity this is now my property
    uint8_t* data_ptr;
    ssize_t length;
    PYBIND11_BYTES_AS_STRING_AND_SIZE(data->ptr(), reinterpret_cast<char**>(&data_ptr), &length);

    // Create our return buffer
    std::string buffer;
    buffer.resize(length + 1);

    // Encode the data
    cobsEncode(data_ptr, length, reinterpret_cast<uint8_t const*>(buffer.data()));

    return py::bytes(buffer);
  }, py::arg("data"), "A function which encodes data using COBS");
  m.def("cobsDecode", [](py::bytes* buffer) {
    // Wrap cobsDecode as def cobsDecode(buffer: bytes) -> bytes:

    // Hoppity skoppity this is now my property
    uint8_t* buffer_ptr;
    ssize_t length;
    PYBIND11_BYTES_AS_STRING_AND_SIZE(buffer->ptr(), reinterpret_cast<char**>(&buffer_ptr), &length);

    // Create our return buffer
    std::string data;
    data.resize(length - 1);

    // Decode the buffer
    cobsDecode(buffer_ptr, length, reinterpret_cast<uint8_t const*>(data.data()));

    return py::bytes(data);
  }, py::arg("buffer"), "A function which decodes a buffer using COBS");
}
