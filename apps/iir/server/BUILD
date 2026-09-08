load("@rules_rust//rust:defs.bzl", "rust_binary")

# axum server: proxies OpenWeatherMap and serves the wasm client bundle.
rust_binary(
    name = "server",
    srcs = [
        "main.rs",
    ],
    edition = "2024",
    tags = ["manual"],
    visibility = ["//apps/iir:__pkg__"],
    deps = [
        "//apps/iir/shared:iir_shared",
        "//lrb/config",
        "//lrb/serve",
        "@crates//:axum",
        "@crates//:env_logger",
        "@crates//:log",
        "@crates//:reqwest",
        "@crates//:tokio",
        "@crates//:tower-http",
    ],
)
