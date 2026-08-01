load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

exports_files(["Cargo.toml"])

# Dependency-free deterministic RNG shared by the Rust games (brm, euc). Must
# stay free of external deps: consumers pull third-party crates from separate
# crate_universe hubs whose types are incompatible with each other.
rust_library(
    name = "rng",
    srcs = ["lib.rs"],
    crate_name = "lrb_rng",
    edition = "2021",
    visibility = ["//visibility:public"],
)

rust_test(
    name = "rng_test",
    crate = ":rng",
    edition = "2021",
)
