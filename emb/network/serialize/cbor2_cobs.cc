#include "emb/network/serialize/cbor2_cobs.hpp"

#include "emb/network/serialize/serializer.hpp"

namespace emb {
namespace network {
namespace serialize {

Cbor2Cobs::Cbor2Cobs() {}

Cbor2Cobs::~Cbor2Cobs() {}

static_assert(SerializerLike<Cbor2Cobs>);

}  // namespace serialize
}  // namespace network
}  // namespace emb
