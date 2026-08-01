load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

exports_files(["Cargo.toml"])

# Pure wire types + the `fraction` helper. No I/O, so it builds for the native
# server and the wasm browser client alike.
rust_library(
    name = "hyd_shared",
    srcs = glob(["src/*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//apps/hyd:__subpackages__"],
    deps = [
        "@hyd_crates//:serde",
    ],
)

rust_test(
    name = "hyd_shared_test",
    crate = ":hyd_shared",
    edition = "2021",
    deps = [
        "@hyd_crates//:serde_json",
    ],
)
