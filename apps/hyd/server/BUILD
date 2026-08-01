load("@rules_rust//rust:defs.bzl", "rust_binary")

exports_files(["Cargo.toml"])

# axum server: Postgres-backed progress CRUD + static serving of the wasm
# client bundle.
rust_binary(
    name = "server",
    srcs = glob(["src/*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//apps/hyd:__pkg__"],
    deps = [
        "//apps/hyd/shared:hyd_shared",
        "//lrb/config",
        "@hyd_crates//:axum",
        "@hyd_crates//:deadpool-postgres",
        "@hyd_crates//:env_logger",
        "@hyd_crates//:log",
        "@hyd_crates//:serde",
        "@hyd_crates//:serde_json",
        "@hyd_crates//:tokio",
        "@hyd_crates//:tokio-postgres",
        "@hyd_crates//:tower-http",
    ],
)
