#include <inttypes.h>
#include <vector>

#include "emb/project/base/base_bh.hpp"
#include "emb/project/robo24/robo24_bh.hpp"

namespace emb {
namespace project {
namespace robo24 {

struct Robo24::Robo24Impl {
    Robo24Impl() {}
    ~Robo24Impl() {}
};

Robo24::Robo24() : impl_(new Robo24Impl()) {}

Robo24::~Robo24() { delete impl_; }

DistanceMeasurement Robo24::get_measurement(const base::Ping &ping) {
    DistanceMeasurement meas;

    meas.distance_mm = 0;
    meas.timestamp_ms = 0;

    return meas;
}

}  // namespace robo24
}  // namespace project
}  // namespace emb
