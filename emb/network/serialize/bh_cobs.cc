#include "emb/network/serialize/bh_cobs.hpp"

#include "emb/network/serialize/serializer.hpp"

namespace emb {
namespace network {
namespace serialize {

BhCobs::BhCobs() {}

BhCobs::~BhCobs() {}

void BhCobs::initialize() {}

static_assert(SerializerLike<BhCobs>);

}  // namespace serialize
}  // namespace network
}  // namespace emb
