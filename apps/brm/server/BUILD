load("@rules_rust//rust:defs.bzl", "rust_binary")

exports_files(["Cargo.toml"])

# Authoritative headless server: axum HTTP (serves the wasm web client) +
# WebSocket + the 30Hz sim loop. Run: `bazel run //apps/brm/server`.
rust_binary(
    name = "server",
    srcs = glob(["src/*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//visibility:public"],
    deps = [
        "//apps/brm/shared:brm_shared",
        "@brm_crates//:axum",
        "@brm_crates//:bincode",
        "@brm_crates//:env_logger",
        "@brm_crates//:futures-util",
        "@brm_crates//:serde",
        "@brm_crates//:tokio",
        "@brm_crates//:tower-http",
    ],
)
