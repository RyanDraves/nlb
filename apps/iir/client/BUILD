load("@rules_rust//rust:defs.bzl", "rust_shared_library")
load("@rules_rust_wasm_bindgen//:defs.bzl", "rust_wasm_bindgen")

exports_files(["Cargo.toml"])

# Leptos CSR client compiled to wasm. Built only through the wasm platform
# transition in //apps/iir:client_wasm_for_web.
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
        "//apps/iir/shared:iir_shared",
        "@iir_crates//:console_error_panic_hook",
        "@iir_crates//:gloo-net",
        "@iir_crates//:leptos",
        "@iir_crates//:serde",
        "@iir_crates//:serde_json",
        "@iir_crates//:wasm-bindgen",
        "@iir_crates//:wasm-bindgen-futures",
    ],
)

# ES-module output (iir_client.js + iir_client_bg.wasm) loaded directly by
# web/index.html — no bundler.
rust_wasm_bindgen(
    name = "iir_client",
    tags = ["manual"],
    target = "web",
    target_arch = "wasm32",
    visibility = ["//apps/iir:__pkg__"],
    wasm_file = ":client_so",
)
