#include <cinttypes>

#include "emb/network/node/node.hpp"
#include "emb/network/serialize/bh_cobs.hpp"
#include "emb/network/transport/serial.hpp"
#include "emb/project/base/base_bh.hpp"
#include "emb/util/log.hpp"

#if __cplusplus < 202100L
#error This code requires C++23 or later
#endif

int main() {
    // Create named variables for the objects to prevent
    // the objects from being destroyed before the node
    emb::network::serialize::BhCobs serializer;
    emb::network::transport::Serial transporter;
    emb::project::base::Base base;

    emb::network::node::Node node(std::move(serializer), std::move(transporter),
                                  std::move(base));

    // Configure the logger instance.
    // We have to configure this here with a lambda to resolve both the
    // template arguments of `node` and `node.publish`
    emb::util::Logger::getInstance().set_publish_function(
        [&node](uint8_t request_id, const emb::project::base::LogMessage &msg) {
            node.publish(request_id, msg);
        });

    node.initialize();

    while (true) {
        node.receive();
    }
}
