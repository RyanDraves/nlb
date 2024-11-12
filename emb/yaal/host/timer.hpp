#include <chrono>

namespace emb {
namespace yaal {
namespace host {

void move_clock(std::chrono::duration<uint64_t, std::micro> duration);

}  // namespace host
}  // namespace yaal
}  // namespace emb
