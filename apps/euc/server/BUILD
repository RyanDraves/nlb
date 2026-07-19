load("@rules_rust//rust:defs.bzl", "rust_binary", "rust_test")

exports_files(["Cargo.toml"])

# Headless authoritative server: lobby of table actors + WebSocket fan-out +
# static file serving for the wasm client bundle.
rust_binary(
    name = "server",
    srcs = glob(["src/*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//apps/euc:__pkg__"],
    deps = [
        "//apps/euc/shared:euc_shared",
        "@euc_crates//:axum",
        "@euc_crates//:env_logger",
        "@euc_crates//:futures-util",
        "@euc_crates//:getrandom",
        "@euc_crates//:hmac",
        "@euc_crates//:log",
        "@euc_crates//:serde",
        "@euc_crates//:serde_json",
        "@euc_crates//:sha2",
        "@euc_crates//:tokio",
        "@euc_crates//:tower-http",
    ],
)

# End-to-end: real router + real WebSocket, auth on, AIs play a full hand.
rust_test(
    name = "euc_server_test",
    crate = ":server",
    edition = "2021",
    tags = ["manual"],
    deps = [
        "@euc_crates//:tokio-tungstenite",
        "@euc_crates//:tower",
    ],
)
