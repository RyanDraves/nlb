#include <cinttypes>
#include <functional>
#include <map>

#include "emb/network/node/node.hpp"
#include "emb/network/serialize/bh_cobs.hpp"
#include "emb/network/transport/comms_transport.hpp"
#include "emb/network/transport/log_transport.hpp"
#include "emb/project/base/base_bh.hpp"
#include "emb/project/punbox/punbox_bh.hpp"
#include "emb/util/log.hpp"

int main() {
    // Create named variables for the objects to prevent
    // the objects from being destroyed before the node
    emb::network::serialize::BhCobs serializer;
    emb::network::transport::CommsTransport &comms =
        emb::network::transport::CommsTransport::getInstance();
    emb::network::transport::LogTransport &logging =
        emb::network::transport::LogTransport::getInstance();
    emb::project::base::Base base;
    emb::project::punbox::Punbox punbox;

    emb::network::node::Node node(std::move(serializer), comms, logging,
                                  std::move(base), std::move(punbox));

    // Configure the logger instance.
    // We have to configure this here with a lambda to resolve both the
    // template arguments of `node` and `node.publish`
    emb::util::Logger::getInstance().set_publish_function(
        [&node](uint8_t request_id, const emb::project::base::LogMessage &msg) {
            node.publish(request_id, msg,
                         emb::network::node::TransportType::LOGGING);
        });

    node.initialize();

    while (true) {
        // `receive` returns within ~10ms on the Pico's serial transport, so
        // this loop also polls the button often enough to debounce it.
        //
        // NOTE: `punbox` shares its (heap-allocated) implementation with the
        // copy moved into `node`, so ticking the local instance is fine.
        node.receive();
        punbox.tick();
    }
}
