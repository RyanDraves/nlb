load("@rules_rust//rust:defs.bzl", "rust_binary", "rust_test")

# Headless authoritative server: lobby of table actors + WebSocket fan-out +
# static file serving for the wasm client bundle.
rust_binary(
    name = "server",
    srcs = glob(["*.rs"]),
    edition = "2021",
    tags = ["manual"],
    visibility = ["//apps/euc:__pkg__"],
    deps = [
        "//apps/euc/shared:euc_shared",
        "@crates//:axum",
        "@crates//:env_logger",
        "@crates//:futures-util",
        "@crates//:getrandom",
        "@crates//:hmac",
        "@crates//:log",
        "@crates//:serde",
        "@crates//:serde_json",
        "@crates//:sha2",
        "@crates//:tokio",
        "@crates//:tower-http",
    ],
)

# End-to-end: real router + real WebSocket, auth on, AIs play a full hand.
rust_test(
    name = "euc_server_test",
    crate = ":server",
    edition = "2021",
    deps = [
        "@crates//:tokio-tungstenite",
        "@crates//:tower",
    ],
)
