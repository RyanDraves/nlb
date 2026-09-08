load("@rules_rust//rust:defs.bzl", "rust_binary", "rust_test")

# tests.rs is `#[cfg(test)] mod tests;`, but pure_bazel mode does no module
# discovery, so gazelle would hoist these test-only crates onto the binary.
# gazelle:rust_ignore_import tokio_tungstenite
# gazelle:rust_ignore_import tower

# Headless authoritative server: lobby of table actors + WebSocket fan-out +
# static file serving for the wasm client bundle.
rust_binary(
    name = "server",
    srcs = [
        "auth.rs",
        "lobby.rs",
        "main.rs",
        "table.rs",
        "tests.rs",
        "ws.rs",
    ],
    edition = "2024",
    tags = ["manual"],
    visibility = ["//apps/euc:__pkg__"],
    deps = [
        "//apps/euc/shared:euc_shared",
        "//lrb/config",
        "//lrb/serve",
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
    edition = "2024",
    # keep: used only by tests.rs, which pure_bazel mode can't attribute.
    deps = [
        "@crates//:tokio-tungstenite",
        "@crates//:tower",
    ],
)
