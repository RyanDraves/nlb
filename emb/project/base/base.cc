
#include <inttypes.h>
#include <vector>

#include "emb/project/base/base_bh.hpp"
#include "emb/project/bootloader/bootloader_bh.hpp"
#include "emb/yaal/flash.hpp"
#include "emb/yaal/watchdog.hpp"

namespace emb {
namespace project {
namespace base {

struct Base::BaseImpl {
    BaseImpl() {}
    ~BaseImpl() {}

    bootloader::SystemFlashPage system;
};

Base::Base() : impl_(new BaseImpl()) {
    // Read the system flash page
    // TODO: This probably fails on a fresh Pico;
    // need to gracefully handle bad deserialization
    auto buffer = yaal::flash_sector_read(0);
    impl_->system = bootloader::SystemFlashPage::deserialize(buffer).first;
}

Base::~Base() { delete impl_; }

LogMessage Base::ping(const Ping &ping) {
    // Create a response message
    LogMessage log_message;
    log_message.message = "Pong!";

    return log_message;
}

FlashPage Base::write_flash_image(const FlashPage &flash_page) {
    FlashPage response;
    response.address = flash_page.address;
    response.read_size = flash_page.read_size;

    // Write to the flash memory opposite of our current app side
    uint32_t app_addr = yaal::kAppAddrB;

    yaal::flash_write(app_addr + flash_page.address, flash_page.data);

    return response;
}

FlashPage Base::read_flash(const FlashPage &flash_page) {
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

FlashSector Base::write_flash_sector(const FlashSector &flash_sector) {
    FlashSector response;
    response.sector = flash_sector.sector;
    response.data = flash_sector.data;

    // Write to the flash memory
    yaal::flash_sector_write(flash_sector.sector, flash_sector.data);

    if (flash_sector.sector == 0) {
        // Update the read system flash page
        impl_->system =
            bootloader::SystemFlashPage::deserialize(flash_sector.data).first;
    }

    return response;
}

FlashSector Base::read_flash_sector(const FlashSector &flash_sector) {
    FlashSector response;
    response.sector = flash_sector.sector;
    auto sector = yaal::flash_sector_read(flash_sector.sector);
    response.data.resize(sector.size());
    memcpy(response.data.data(), sector.data(), sector.size());

    return response;
}

Ping Base::reset(const Ping &ping) {
    // Reset the device
    emb::yaal::force_watchdog_reset();
}

}  // namespace base
}  // namespace project
}  // namespace emb
