
#include <inttypes.h>
#include <string>
#include <vector>

#include "emb/project/base/base_bh.hpp"
#include "emb/yaal/flash.hpp"

#include <iostream>

namespace emb {
namespace project {
namespace base {

LogMessage Base::ping(const Ping &ping) {
    // Create a response message
    LogMessage log_message;
    log_message.message = "Pong " + std::to_string(ping.ping) + "!";

    return log_message;
}

FlashPage Base::flash_page(const FlashPage &flash_page) {
    FlashPage response;
    response.address = flash_page.address;
    response.read_size = flash_page.read_size;
    response.data.resize(flash_page.read_size);

    // TODO: Implement the flash page handler

    return response;
}

FlashPage Base::read_flash_page(const FlashPage &flash_page) {
    FlashPage response;
    response.address = flash_page.address;
    response.read_size = flash_page.read_size;
    response.data.resize(flash_page.read_size);

    // Read from the flash memory
    const uint8_t *flash_ptr = yaal::get_flash_ptr(flash_page.address);
    for (uint32_t i = 0; i < flash_page.read_size; i++) {
        response.data[i] = flash_ptr[i];
    }

    return response;
}

}  // namespace base
}  // namespace project
}  // namespace emb
