#include "emb/network/transport/serial.hpp"
#include "pico/stdlib.h"

namespace emb {
namespace network {
namespace transport {

struct Serial::SerialImpl {
    uint16_t rx_size = 0;
};

Serial::Serial() : impl_(new SerialImpl) {
    stdio_init_all();
    stdio_set_translate_crlf(&stdio_usb, false);
}

Serial::~Serial() { delete impl_; }

void Serial::send(const std::span<uint8_t> &data) {
    // Send the message over the wire
    //
    // `stdout` is buffered on newlines, so we need to use `stderr` to
    // write the message immediately
    fwrite(data.data(), 1, data.size(), stderr);
}

std::span<uint8_t> Serial::receive(std::span<uint8_t> buffer) {
    int16_t rc = getchar_timeout_us(10'000);
    while (rc != PICO_ERROR_TIMEOUT && impl_->rx_size < buffer.size()) {
        buffer[impl_->rx_size++] = rc;
        // TODO: Configure frame boundary
        if (rc == 0x00) {
            // Subtract the frame separator
            impl_->rx_size--;
            // Frame complete
            uint16_t rx_size = impl_->rx_size;
            impl_->rx_size = 0;
            return buffer.subspan(0, rx_size);
        }

        rc = getchar_timeout_us(1000);
    }

    if (impl_->rx_size == buffer.size()) {
        // Buffer full, reset
        impl_->rx_size = 0;
    }

    // Return an empty span upon timeout
    return {};
}

}  // namespace transport
}  // namespace network
}  // namespace emb
