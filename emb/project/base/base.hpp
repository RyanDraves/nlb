#pragma once

#include <inttypes.h>
#include <string>
#include <vector>

#include "emb/network/node/node.hpp"
#include "emb/network/serialize/serializer.hpp"
#include "emb/network/transport/transporter.hpp"
#include "emb/yaal/flash.hpp"

namespace emb {
namespace project {

// TODO: Generate everything in this file except the handler definitions
struct LogMessage {
    std::string message;
};

struct FlashPage {
    uint32_t address;
    uint16_t read_size;
    std::vector<uint8_t> data;
};

struct Ping {
    uint32_t ping;
};

class Base {
  public:
    Base() {}
    ~Base() {}

    template <network::serialize::SerializerLike S,
              network::transport::TransporterLike T, class... Projects>
    void register_handlers(network::node::Node<S, T, Projects...> &node) {
        node.template register_handler<Ping, LogMessage>(
            0x00, std::bind(&Base::ping, this, std::placeholders::_1));
        node.template register_handler<FlashPage, FlashPage>(
            0x01, std::bind(&Base::flash_page, this, std::placeholders::_1));
    }

    LogMessage ping(const Ping &ping) {
        // Create a response message
        LogMessage log_message;
        log_message.message = "Pong " + std::to_string(ping.ping) + "!";

        return log_message;
    }

    FlashPage flash_page(const FlashPage &flash_page) {
        FlashPage response;
        response.address = flash_page.address;
        response.read_size = flash_page.read_size;
        response.data.resize(flash_page.read_size);

        if (!flash_page.data.size()) {
            // This is a write request
        } else {
            // This is a read request

            // Read from the flash memory
            const uint8_t *flash_ptr = yaal::get_flash_ptr(flash_page.address);
            for (int i = 0; i < flash_page.read_size; i++) {
                response.data.push_back(flash_ptr[i]);
            }
        }

        return response;
    }
};

}  // namespace project
}  // namespace emb
