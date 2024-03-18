#include <stdio.h>
#include <stdlib.h>
#include <algorithm>

#include "pb_encode.h"
#include "pb_decode.h"
#include "pico/stdlib.h"

#if __cplusplus < 202100L
#error This code requires C++23 or later
#endif

#include "emb/playground/system.pb.h"
#include "emb/util/cobs.hpp"

class Hello {
private:
    constexpr static size_t kBufSize = 254;
public:
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
        size_t decodedLength = cobsDecode(rx_buffer_, rx_size_ - 1, rx_buffer_);

        // Decode the incoming message
        pb_istream_t stream = pb_istream_from_buffer(rx_buffer_, decodedLength);
        has_message_ = pb_decode(&stream, emb_Config_fields, &config_);
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

        // Encode the outgoing message
        pb_ostream_t stream = pb_ostream_from_buffer(tx_buffer_, kBufSize);
        bool success = pb_encode(&stream, emb_Config_fields, &config_);

        // COBS encode the message
        size_t encoded_length = cobsEncode(tx_buffer_, stream.bytes_written, tx_buffer_raw_);
        // Our COBS encode does not output the delimiter byte, so we need to
        // manually add it
        tx_buffer_raw_[encoded_length] = 0x00;

        // Send the message over the wire
        //
        // `stdout` is buffered on newlines, so we need to use `stderr` to
        // write the message immediately
        fwrite(tx_buffer_raw_, 1, encoded_length + 1, stderr);
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

    emb_Config config_ = emb_Config_init_default;

    // A neat trick with COBS encoding is that we can write the encoded message
    // in-place, provided that our data <overhead_bytes> bytes into the buffer
    //
    // Store the encoded message in the "raw" buffer
    uint8_t tx_buffer_raw_[kBufSize + 1];
    // And store our record message in the "normal" buffer
    uint8_t* tx_buffer_ = tx_buffer_raw_ + 1;

    // We can write the decoded message in-place as well
    uint8_t rx_buffer_[kBufSize];

    bool has_message_ = false;
    uint8_t rx_size_ = 0;
};

int main() {
    stdio_init_all();
    stdio_set_translate_crlf(&stdio_usb, false);

    Hello hello;
    while (true) {
        hello.decode();
        hello.process();
        hello.encode();
        // hello.say();
        // sleep_ms(1000);
    }
}
