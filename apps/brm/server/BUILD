load("@rules_rust//rust:defs.bzl", "rust_binary")

# Authoritative headless server: axum HTTP (serves the wasm web client) +
# WebSocket + the 30Hz sim loop. Run: `bazel run //apps/brm/server`.
rust_binary(
    name = "server",
    srcs = [
        "game.rs",
        "main.rs",
        "ws.rs",
    ],
    edition = "2024",
    tags = ["manual"],
    visibility = ["//visibility:public"],
    deps = [
        "//apps/brm/shared:brm_shared",
        "//lrb/config",
        "//lrb/serve",
        "@crates//:axum",
        "@crates//:bincode",
        "@crates//:env_logger",
        "@crates//:futures-util",
        "@crates//:tokio",
        "@crates//:tower-http",
    ],
)
