load("@rules_rust//rust:defs.bzl", "rust_shared_library")
load("@rules_rust//wasm_bindgen:defs.bzl", "rust_wasm_bindgen")

rust_shared_library(
    name = "game_of_life_so",
    srcs = [
        "lib.rs",
        "utils.rs",
    ],
    rustc_flags = [
        "--crate-type=cdylib",
        # Small code size
        "--codegen=opt-level=z",
    ],
    target_compatible_with = [
        "@platforms//cpu:wasm32",
    ],
    deps = [
        "@crates//:console_error_panic_hook",
        "@crates//:lazy_static",
        "@crates//:spin",
        "@crates//:wasm-bindgen",
        "@crates//:web-sys",
        "@crates//:wee_alloc",
    ],
)

rust_wasm_bindgen(
    name = "game_of_life",
    target = "bundler",
    target_arch = "wasm32",
    visibility = ["//visibility:public"],
    wasm_file = ":game_of_life_so",
)
