load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

exports_files(["Cargo.toml"])

# Pure, deterministic game model + wire protocol. No I/O, so it builds for the
# native server, the native client, and the wasm browser client alike.
rust_library(
    name = "brm_shared",
    srcs = glob(["src/*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//apps/brm:__subpackages__"],
    deps = [
        "@brm_crates//:serde",
    ],
)

rust_test(
    name = "brm_shared_test",
    crate = ":brm_shared",
    edition = "2021",
)
