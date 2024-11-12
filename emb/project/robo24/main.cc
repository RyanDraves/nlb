#include <cinttypes>
#include <functional>
#include <map>

#include "emb/network/node/node.hpp"
#include "emb/network/serialize/bh_cobs.hpp"
#include "emb/network/transport/serial.hpp"
#include "emb/project/base/base_bh.hpp"
#include "emb/project/robo24/robo24_bh.hpp"

int main() {
    // Create named variables for the objects to prevent
    // the objects from being destroyed before the node
    emb::network::serialize::BhCobs serializer;
    emb::network::transport::Serial transporter;
    emb::project::base::Base base;
    emb::project::robo24::Robo24 robo24;

    emb::network::node::Node node(std::move(serializer), std::move(transporter),
                                  std::move(base), std::move(robo24));

    while (true) {
        node.receive();
    }
}
