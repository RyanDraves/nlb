load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

# Config helpers shared by the Rust web apps (hyd, iir)
rust_library(
    name = "config",
    srcs = ["lib.rs"],
    crate_name = "lrb_config",
    edition = "2021",
    visibility = ["//visibility:public"],
)

rust_test(
    name = "config_test",
    crate = ":config",
    edition = "2021",
)
