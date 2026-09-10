load("@rules_rust//rust:defs.bzl", "rust_binary", "rust_test")

# Build-time bundler behind //bzl/macros:monofile.bzl. Shares
# lrb_monofile::shell::render with the wasm runtime, so the self-reproduction
# fixed point is checked on every build rather than hoped for.
rust_binary(
    name = "bundler",
    srcs = ["main.rs"],
    edition = "2024",
    visibility = ["//visibility:public"],
    deps = ["//lrb/monofile"],
)

rust_test(
    name = "bundler_test",
    crate = ":bundler",
    edition = "2024",
)
