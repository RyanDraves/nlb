load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

exports_files(["Cargo.toml"])

# Pure, deterministic Euchre rules engine + wire protocol. No I/O, so it
# builds for the native server, the wasm browser client, and bots alike.
rust_library(
    name = "euc_shared",
    srcs = glob(["src/*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//apps/euc:__subpackages__"],
    deps = [
        "//lrb/rng",
        "@euc_crates//:serde",
    ],
)

rust_test(
    name = "euc_shared_test",
    crate = ":euc_shared",
    edition = "2021",
    deps = [
        "@euc_crates//:serde_json",
    ],
)
