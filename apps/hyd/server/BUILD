load("@rules_rust//rust:defs.bzl", "rust_binary")

# axum server: Postgres-backed progress CRUD + static serving of the wasm
# client bundle.
rust_binary(
    name = "server",
    srcs = glob(["*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//apps/hyd:__pkg__"],
    deps = [
        "//apps/hyd/shared:hyd_shared",
        "//lrb/config",
        "//lrb/serve",
        "@crates//:axum",
        "@crates//:deadpool-postgres",
        "@crates//:env_logger",
        "@crates//:log",
        "@crates//:serde",
        "@crates//:serde_json",
        "@crates//:tokio",
        "@crates//:tokio-postgres",
        "@crates//:tower-http",
    ],
)
