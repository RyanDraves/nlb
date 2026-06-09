#pragma once

namespace emb {
namespace project {
namespace punbox {

// Service the button from the main loop.
//
// This is a free function because the buffham-generated `Punbox` class has a
// fixed shape; it forwards to the `Punbox` instance, which must be
// constructed first.
void tick();

}  // namespace punbox
}  // namespace project
}  // namespace emb
