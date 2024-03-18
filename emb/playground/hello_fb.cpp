#include <stdio.h>
#include <stdlib.h>
#include <algorithm>

#include "pico/stdlib.h"
#include "flatbuffers/flatbuffers.h"

#if __cplusplus < 202100L
#error This code requires C++23 or later
#endif

#include "emb/playground/system_generated.h"
#include "emb/util/cobs.hpp"

template <size_t BufferSize>
class StaticAllocator : public flatbuffers::Allocator {
 public:
    StaticAllocator() {}

    uint8_t* allocate(size_t size) override {
        // Ignore the size, we always return the same buffer
        return buffer_;
    }

    void deallocate(uint8_t* p, size_t size) override {
        // Do nothing
        return;
    }

 private:
    uint8_t buffer_[BufferSize];
};

class Hello {
private:
    constexpr static size_t kBufSize = 254;
public:
    Hello() : tx_builder_(kBufSize + 1, &tx_buffer_allocator_),
              tx_buffer_raw_(tx_buffer_),
              tx_buffer_(tx_buffer_raw_ + 1),
              rx_builder_(kBufSize + 1, &rx_buffer_allocator_),
              rx_buffer_(rx_builder_.GetBufferPointer()) {
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
        size_t decodedLength = cobsDecode(rx_buffer_, rx_size_ - 1, rx_buffer_);

        // Decode the incoming message
        config_ = emb::GetMutableConfig(rx_buffer_);
        has_message_ = true;
    }

    void process() {
        if (!has_message_) {
            return;
        }

        config_->mutate_ping(config_->ping() + 1);
    }

    void encode() {
        if (!has_message_) {
            return;
        }

        // Copy the message into the tx buffer
        tx_builder_.Clear();
        auto config_mem = emb::CreateConfig(tx_builder_, config_->ping());
        tx_builder_.Finish(config_mem);

        // COBS encode the message
        // size_t encoded_length = cobsEncode(tx_buffer_, stream.bytes_written, tx_buffer_raw_);
        size_t encoded_length = cobsEncode(tx_buffer_, tx_builder_.GetSize(), tx_buffer_raw_);
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

    emb::Config* config_;

    StaticAllocator<kBufSize + 1> tx_buffer_allocator_;
    flatbuffers::FlatBufferBuilder tx_builder_;
    // A neat trick with COBS encoding is that we can write the encoded message
    // in-place, provided that our data <overhead_bytes> bytes into the buffer
    //
    // Store the encoded message in the "raw" buffer
    uint8_t* tx_buffer_raw_;
    // And store our record message in the "normal" buffer
    uint8_t* tx_buffer_;

    StaticAllocator<kBufSize + 1> rx_buffer_allocator_;
    flatbuffers::FlatBufferBuilder rx_builder_;
    // We can write the decoded message in-place as well
    uint8_t* rx_buffer_;

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
