load("@rules_rust//rust:defs.bzl", "rust_shared_library")
load("//bzl/macros:monofile.bzl", "monofile_html")

# Notes scratchpad on raw web-sys. Half of the Phase 0 framework bake-off; see
# ../notes_leptos for the Leptos build of the same app.
rust_shared_library(
    name = "notes_sys_so",
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
        "@crates//:wasm-bindgen",
        "@crates//:wasm-bindgen-futures",
        "@crates//:web-sys",
    ],
)

monofile_html(
    name = "notes_sys",
    content_type = "text/plain",
    # Also exercises the macro's `payload` attr: a monofile normally ships
    # carrying a document rather than empty.
    payload = "sample.txt",
    visibility = ["//visibility:public"],
    wasm_lib = ":notes_sys_so",
)
