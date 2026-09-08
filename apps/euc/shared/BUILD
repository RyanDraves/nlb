load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")

# Pure, deterministic Euchre rules engine + wire protocol. No I/O, so it
# builds for the native server, the wasm browser client, and bots alike.
rust_library(
    name = "euc_shared",
    srcs = [
        "ai.rs",
        "cards.rs",
        "game.rs",
        "legal.rs",
        "lib.rs",
        "protocol.rs",
        "rules.rs",
        "score.rs",
        "tests.rs",
        "view.rs",
    ],
    edition = "2024",
    tags = ["manual"],
    visibility = ["//apps/euc:__subpackages__"],
    deps = [
        "//lrb/rng",
        "@crates//:serde",
    ],
)

rust_test(
    name = "euc_shared_test",
    crate = ":euc_shared",
    edition = "2024",
    deps = ["@crates//:serde_json"],
)
