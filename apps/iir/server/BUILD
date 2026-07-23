load("@rules_rust//rust:defs.bzl", "rust_binary")

exports_files(["Cargo.toml"])

# axum server: proxies OpenWeatherMap and serves the wasm client bundle.
rust_binary(
    name = "server",
    srcs = glob(["src/*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//apps/iir:__pkg__"],
    deps = [
        "//apps/iir/shared:iir_shared",
        "//lrb/config",
        "@iir_crates//:axum",
        "@iir_crates//:env_logger",
        "@iir_crates//:log",
        "@iir_crates//:reqwest",
        "@iir_crates//:serde",
        "@iir_crates//:serde_json",
        "@iir_crates//:tokio",
        "@iir_crates//:tower-http",
    ],
)
