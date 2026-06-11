#include "emb/network/transport/serial.hpp"
#include "pico/stdlib.h"

#include <cstdio>
#include <cstring>

namespace emb {
namespace network {
namespace transport {

struct Serial::SerialImpl {
    uint16_t rx_size = 0;
    // Bytes read past a frame boundary, carried over to the next `receive`
    // call. Sized to match the largest `receive` buffer (`kBufSize`).
    uint8_t pending[1536];
    uint16_t pending_size = 0;
};

Serial::Serial() : impl_(new SerialImpl) {}

Serial::~Serial() { delete impl_; }

void Serial::initialize() {
    if (initialized_) {
        return;
    }

    // Initialize the serial port
    stdio_init_all();
    stdio_set_translate_crlf(&stdio_usb, false);

    initialized_ = true;
}

void Serial::send(const std::span<uint8_t> &data) {
    // Send the message over the wire
    //
    // `stdout` is buffered on newlines, so we need to use `stderr` to
    // write the message immediately
    fwrite(data.data(), 1, data.size(), stderr);
}

std::span<uint8_t> Serial::receive(std::span<uint8_t> buffer) {
    // Restore any bytes read past the previous frame's boundary
    if (impl_->pending_size) {
        memcpy(buffer.data() + impl_->rx_size, impl_->pending,
               impl_->pending_size);
        impl_->rx_size += impl_->pending_size;
        impl_->pending_size = 0;
    }

    // Read in bulk until a frame separator shows up, the buffer fills, or
    // we time out. Reading byte-by-byte with `getchar_timeout_us` costs
    // ~50us/byte, which dominates large transfers like flash images.
    uint16_t scanned = 0;
    absolute_time_t deadline = make_timeout_time_us(10'000);
    while (true) {
        // TODO: Configure frame boundary
        for (uint16_t i = scanned; i < impl_->rx_size; i++) {
            if (buffer[i] == 0x00) {
                // Stash bytes past the frame for the next call
                impl_->pending_size = impl_->rx_size - i - 1;
                memcpy(impl_->pending, buffer.data() + i + 1,
                       impl_->pending_size);
                impl_->rx_size = 0;
                // Frame complete (frame separator excluded)
                return buffer.subspan(0, i);
            }
        }
        scanned = impl_->rx_size;

        if (impl_->rx_size == buffer.size()) {
            // Buffer full, reset
            impl_->rx_size = 0;
            return {};
        }

        int rc = stdio_get_until((char *)buffer.data() + impl_->rx_size,
                                 buffer.size() - impl_->rx_size, deadline);
        if (rc <= 0) {
            // Return an empty span upon timeout, keeping any partial frame
            // accumulated so far
            return {};
        }
        impl_->rx_size += rc;
        deadline = make_timeout_time_us(1'000);
    }
}

}  // namespace transport
}  // namespace network
}  // namespace emb
