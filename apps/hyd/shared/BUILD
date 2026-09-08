load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

# Pure wire types + the `fraction` helper. No I/O, so it builds for the native
# server and the wasm browser client alike.
rust_library(
    name = "hyd_shared",
    srcs = glob(["*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//apps/hyd:__subpackages__"],
    deps = [
        "@crates//:serde",
    ],
)

rust_test(
    name = "hyd_shared_test",
    crate = ":hyd_shared",
    edition = "2021",
    deps = [
        "@crates//:serde_json",
    ],
)
