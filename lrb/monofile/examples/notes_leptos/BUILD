load("@rules_rust//rust:defs.bzl", "rust_shared_library")
load("//bzl/macros:monofile.bzl", "monofile_html")

# Notes scratchpad on Leptos. Half of the Phase 0 framework bake-off; see
# ../notes_sys for the raw web-sys build of the same app.
rust_shared_library(
    name = "notes_leptos_so",
    srcs = ["lib.rs"],
    edition = "2024",
    rustc_flags = [
        "--crate-type=cdylib",
        # Small code size for the single-file download.
        "--codegen=opt-level=z",
    ],
    target_compatible_with = ["@platforms//cpu:wasm32"],
    deps = [
        "//lrb/monofile",
        "@crates//:console_error_panic_hook",
        "@crates//:leptos",
        "@crates//:wasm-bindgen",
        "@crates//:wasm-bindgen-futures",
        "@crates//:web-sys",
    ],
)

monofile_html(
    name = "notes_leptos",
    content_type = "text/plain",
    visibility = ["//visibility:public"],
    wasm_lib = ":notes_leptos_so",
)
