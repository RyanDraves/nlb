load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

exports_files(["Cargo.toml"])

# Pure wire types + the `is_raining` classifier. No I/O, so it builds for the
# native server and the wasm browser client alike.
rust_library(
    name = "iir_shared",
    srcs = glob(["src/*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//apps/iir:__subpackages__"],
    deps = [
        "@iir_crates//:serde",
    ],
)

rust_test(
    name = "iir_shared_test",
    crate = ":iir_shared",
    edition = "2021",
    tags = ["manual"],
    deps = [
        "@iir_crates//:serde_json",
    ],
)
