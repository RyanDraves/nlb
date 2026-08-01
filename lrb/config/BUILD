load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

exports_files(["Cargo.toml"])

# Dependency-free config helpers shared by the Rust web apps (hyd, iir). Must
# stay free of external deps: consumers pull third-party crates from separate
# crate_universe hubs whose types are incompatible with each other. See
# //lrb/rng for the same rationale.
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
