load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

# Deterministic RNG shared by the Rust games (brm, euc)
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
