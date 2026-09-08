load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

# axum server plumbing shared by the Rust web apps (brm, euc, hyd, iir): the
# no-store cache policy, the `*_WEB_DIR` lookup, and the bind/serve tail.
rust_library(
    name = "serve",
    srcs = ["lib.rs"],
    crate_name = "lrb_serve",
    edition = "2024",
    visibility = ["//visibility:public"],
    deps = [
        "@crates//:axum",
        "@crates//:tokio",
    ],
)

rust_test(
    name = "serve_test",
    crate = ":serve",
    edition = "2024",
    deps = ["@crates//:tower"],
)
