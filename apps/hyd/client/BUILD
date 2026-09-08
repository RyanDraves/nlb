load("@rules_rust//rust:defs.bzl", "rust_shared_library")
load("@rules_rust_wasm_bindgen//:defs.bzl", "rust_wasm_bindgen")

# Leptos CSR client compiled to wasm. Built only through the wasm platform
# transition in //apps/hyd:client_wasm_for_web.
rust_shared_library(
    name = "client_so",
    srcs = glob(["*.rs"]),
    edition = "2021",
    rustc_flags = [
        "--crate-type=cdylib",
        # Small code size for the web download.
        "--codegen=opt-level=z",
    ],
    tags = ["manual"],
    target_compatible_with = ["@platforms//cpu:wasm32"],
    deps = [
        "//apps/hyd/shared:hyd_shared",
        "@crates//:console_error_panic_hook",
        "@crates//:gloo-net",
        "@crates//:gloo-timers",
        "@crates//:leptos",
        "@crates//:serde",
        "@crates//:serde_json",
        "@crates//:wasm-bindgen",
        "@crates//:wasm-bindgen-futures",
    ],
)

# ES-module output (hyd_client.js + hyd_client_bg.wasm) loaded directly by
# web/index.html — no bundler.
rust_wasm_bindgen(
    name = "hyd_client",
    tags = ["manual"],
    target = "web",
    target_arch = "wasm32",
    visibility = ["//apps/hyd:__pkg__"],
    wasm_file = ":client_so",
)
