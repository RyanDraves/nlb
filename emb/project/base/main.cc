#include <functional>
#include <inttypes.h>
#include <map>

#include "emb/network/node/node.hpp"
#include "emb/network/serialize/cbor2_cobs.hpp"
#include "emb/network/transport/serial.hpp"
#include "emb/project/base/base.hpp"

#if __cplusplus < 202100L
#error This code requires C++23 or later
#endif

int main() {
    // Create named variables for the objects to prevent
    // the objects from being destroyed before the node
    emb::network::serialize::Cbor2Cobs serializer;
    emb::network::transport::Serial transporter;
    emb::project::Base base;

    emb::network::node::Node node(std::move(serializer), std::move(transporter),
                                  std::move(base));

    while (true) {
        node.receive();
    }
}
