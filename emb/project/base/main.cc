#include <cinttypes>
#include <functional>
#include <map>

#include "emb/network/node/node.hpp"
#include "emb/network/serialize/bh_cobs.hpp"
#include "emb/network/transport/serial.hpp"
#include "emb/project/base/base_bh.hpp"

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

    while (true) {
        node.receive();
    }
}
