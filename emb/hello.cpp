#include <stdio.h>
#include <stdlib.h>
#include <algorithm>
#include <vector>
#include <functional>
#include <map>

#include "nlohmann/json.hpp"
#include "pico/stdlib.h"
#include "hardware/flash.h"

#if __cplusplus < 202100L
#error This code requires C++23 or later
#endif

#include "emb/util/cobs.hpp"


namespace emb {

using json = nlohmann::json;

struct LogMessage {
    std::string message;

    NLOHMANN_DEFINE_TYPE_INTRUSIVE(LogMessage, message);
};


struct FlashPage {
    uint32_t address;
    uint16_t read_size;
    std::vector<uint8_t> data;

    NLOHMANN_DEFINE_TYPE_INTRUSIVE(FlashPage, address, read_size, data);
};


struct Ping {
    uint32_t ping;

    NLOHMANN_DEFINE_TYPE_INTRUSIVE(Ping, ping);
};

class Hello {
private:
    constexpr static size_t kBufSize = 1024;
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

        // COBS decode the message; subtract 1 to account for the message ID
        rx_msg_size_ = cobsDecode(rx_buffer_.data(), rx_size_ - 1, rx_buffer_.data()) - 1;

        // Check if the first byte is a valid message ID
        if (rx_msg_size_ == 0 || message_handlers_.find(rx_buffer_[0]) == message_handlers_.end()) {
            return;
        }

        // Call the appropriate message handler
        message_handlers_.at(rx_buffer_[0])();
    }

    void ping() {
        // Receive a Ping message from the incoming buffer
        Ping ping = json::from_cbor(rx_buffer_.data() + 1, rx_buffer_.data() + 1 + rx_msg_size_);

        // Create a response message
        LogMessage log_message;
        log_message.message = "Pong " + std::to_string(ping.ping) + "!";
        // Encode the outgoing message
        tx_buffer_.clear();
        tx_buffer_.push_back(0x00);  // Padding for in-place COBS encoding
        // Add the message ID
        tx_buffer_.push_back(0x02);
        json::to_cbor(log_message, tx_buffer_);
        has_tx_message_ = true;
    }

    void flash_page() {
        // Receive a FlashPage emssage from the incoming buffer
        FlashPage flash_page = json::from_cbor(rx_buffer_.data() + 1,  rx_buffer_.data() + 1 + rx_msg_size_);

        if (!flash_page.data.size()) {
            // This is a write request

            // Create a response message
            LogMessage log_message;
            // log_message.message = "Received FlashPage at address " + std::to_string(flash_page.address) + "!";

            const uint8_t* flash_ptr = (const uint8_t*)(XIP_BASE + flash_page.address);
            for (int i = 0; i < flash_page.read_size; i++) {
                log_message.message += std::to_string(flash_ptr[i]) + " ";
            }

            // Encode the outgoing message
            tx_buffer_.clear();
            tx_buffer_.push_back(0x00);  // Padding for in-place COBS encoding
            // Add the message ID
            tx_buffer_.push_back(0x02);
            json::to_cbor(log_message, tx_buffer_);
            has_tx_message_ = true;
        }
        else {
            // This is a read request

            // Create a response message
            FlashPage response;
            response.address = flash_page.address;
            response.read_size = flash_page.read_size;
            response.data.reserve(flash_page.read_size);

            // Read from the flash memory
            // The flash is memory-mapped at XIP_BASE
            const uint8_t* flash_ptr = (const uint8_t*)(XIP_BASE + flash_page.address);
            for (int i = 0; i < flash_page.read_size; i++) {
                response.data.push_back(flash_ptr[i]);
            }

            // Encode the outgoing message
            tx_buffer_.clear();
            tx_buffer_.push_back(0x00);  // Padding for in-place COBS encoding
            // Add the message ID
            tx_buffer_.push_back(0x01);
            json::to_cbor(response, tx_buffer_);
            has_tx_message_ = true;
        }
    }

    void encode() {
        if (!has_tx_message_) {
            return;
        }

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

    // Map message IDs to function pointers
    const std::unordered_map<uint8_t, std::function<void()>> message_handlers_ = {
        {0x00, std::bind(&Hello::ping, this)},
        {0x01, std::bind(&Hello::flash_page, this)},
    };

    // A neat trick with COBS encoding is that we can write the encoded message
    // in-place, provided that our data is <overhead_bytes> bytes into the buffer;
    // we'll manipulate the buffer to make this true
    std::vector<uint8_t> tx_buffer_;

    // We can write the decoded message in-place as well
    std::vector<uint8_t> rx_buffer_;

    size_t rx_msg_size_;

    uint8_t rx_size_ = 0;
    bool has_tx_message_ = false;
};

}  // namespace emb

int main() {
    stdio_init_all();
    stdio_set_translate_crlf(&stdio_usb, false);

    emb::Hello hello;
    while (true) {
        hello.decode();
        hello.encode();
        // sleep_ms(1000);
    }
}
