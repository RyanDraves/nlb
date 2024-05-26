#include <stdio.h>
#include <stdlib.h>
#include <algorithm>
#include <vector>

#include "nlohmann/json.hpp"
#include "pico/stdlib.h"

#if __cplusplus < 202100L
#error This code requires C++23 or later
#endif

#include "emb/util/cobs.hpp"


namespace emb {

using json = nlohmann::json;

struct Config {
    uint32_t ping = 0;

    NLOHMANN_DEFINE_TYPE_INTRUSIVE(Config, ping);
};


class Hello {
private:
    constexpr static size_t kBufSize = 254;
public:
    Hello() {
        // Reserve capacity for the outgoing buffer
        tx_buffer_.reserve(kBufSize + 1);
        // Statically allocate the incoming buffer
        rx_buffer_.resize(kBufSize);
    }

    void say() {
        char buffer[] = "Hello, world!\n";
        // printf("Hello, world! %ld\n", config_.ping);
        fwrite(buffer, 1, sizeof(buffer), stdout);
    }

    void decode() {
        // Read the incoming message from the wire
        //
        // This is setup to idle until a message is received
        while (!read_frame()) {}

        // COBS decode the message
        size_t decodedLength = cobsDecode(rx_buffer_.data(), rx_size_ - 1, rx_buffer_.data());

        // Decode the incoming message
        config_ = json::from_cbor(rx_buffer_.data(), decodedLength);
        has_message_ = true;
    }

    void process() {
        if (!has_message_) {
            return;
        }

        config_.ping++;
    }

    void encode() {
        if (!has_message_) {
            return;
        }

        tx_buffer_.clear();

        // Encode the outgoing message
        tx_buffer_.push_back(0);  // Padding for in-place COBS encoding
        json::to_cbor(config_, tx_buffer_);

        // COBS encode the message
        size_t encoded_length = cobsEncode(tx_buffer_.data() + 1, tx_buffer_.size() - 1, tx_buffer_.data());
        // Our COBS encode does not output the delimiter byte, so we need to
        // manually add it
        tx_buffer_.push_back(0);

        // Send the message over the wire
        //
        // `stdout` is buffered on newlines, so we need to use `stderr` to
        // write the message immediately
        fwrite(tx_buffer_.data(), 1, encoded_length + 1, stderr);
    }

private:
    bool read_frame() {
        // Read the incoming message from the wire
        int16_t rc = getchar_timeout_us(1000);
        rx_size_ = 0;
        has_message_ = false;
        while (rc != PICO_ERROR_TIMEOUT) {
            rx_buffer_[rx_size_++] = rc;
            if (rc == 0x00) {
                // Frame complete
                return true;
            }

            rc = getchar_timeout_us(1000);
        }

        return false;
    }

    Config config_;

    // A neat trick with COBS encoding is that we can write the encoded message
    // in-place, provided that our data is <overhead_bytes> bytes into the buffer;
    // we'll manipulate the buffer to make this true
    std::vector<uint8_t> tx_buffer_;

    // We can write the decoded message in-place as well
    std::vector<uint8_t> rx_buffer_;

    bool has_message_ = false;
    uint8_t rx_size_ = 0;
};

}  // namespace emb

int main() {
    stdio_init_all();
    stdio_set_translate_crlf(&stdio_usb, false);

    emb::Hello hello;
    while (true) {
        hello.decode();
        hello.process();
        hello.encode();
        // sleep_ms(1000);
    }
}
