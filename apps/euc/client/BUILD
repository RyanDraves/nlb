load("@rules_rust//rust:defs.bzl", "rust_shared_library")
load("@rules_rust_wasm_bindgen//:defs.bzl", "rust_wasm_bindgen")

exports_files(["Cargo.toml"])

# Leptos CSR client compiled to wasm. Built only through the wasm platform
# transition in //apps/euc:client_wasm_for_web.
rust_shared_library(
    name = "client_so",
    srcs = glob(["src/*.rs"]),
    edition = "2021",
    rustc_flags = [
        "--crate-type=cdylib",
        # Small code size for the web download.
        "--codegen=opt-level=z",
    ],
    tags = ["manual"],
    target_compatible_with = ["@platforms//cpu:wasm32"],
    deps = [
        "//apps/euc/shared:euc_shared",
        "@euc_crates//:console_error_panic_hook",
        "@euc_crates//:js-sys",
        "@euc_crates//:leptos",
        "@euc_crates//:serde",
        "@euc_crates//:serde_json",
        "@euc_crates//:wasm-bindgen",
        "@euc_crates//:wasm-bindgen-futures",
        "@euc_crates//:web-sys",
    ],
)

# ES-module output (euc_client.js + euc_client_bg.wasm) loaded directly by
# web/index.html — no bundler.
rust_wasm_bindgen(
    name = "euc_client",
    tags = ["manual"],
    target = "web",
    target_arch = "wasm32",
    visibility = ["//apps/euc:__pkg__"],
    wasm_file = ":client_so",
)
