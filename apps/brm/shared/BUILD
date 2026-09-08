load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

# Pure, deterministic game model + wire protocol. No I/O, so it builds for the
# native server, the native client, and the wasm browser client alike.
rust_library(
    name = "brm_shared",
    srcs = [
        "entity.rs",
        "lib.rs",
        "map.rs",
        "protocol.rs",
        "sim.rs",
        "state.rs",
        "tests.rs",
        "tuning.rs",
    ],
    edition = "2024",
    tags = ["manual"],
    visibility = ["//apps/brm:__subpackages__"],
    deps = [
        "//lrb/rng",
        "@crates//:serde",
    ],
)

rust_test(
    name = "brm_shared_test",
    crate = ":brm_shared",
    edition = "2024",
)
