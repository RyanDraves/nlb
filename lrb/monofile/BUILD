load("@rules_rust//rust:defs.bzl", "rust_library", "rust_test")
load("//bzl/macros:python.bzl", "py_test")

exports_files([
    "boot.js",
    "shell.html",
])

# Core for single-file, self-reproducing web apps: the payload framing and the
# shell templating that let a wasm app rebuild its own .html on save.
# `payload.rs` and `shell.rs` are pure and host-tested; `web.rs` is the wasm-only
# DOM and File System Access glue.
rust_library(
    name = "monofile",
    srcs = [
        "lib.rs",
        "payload.rs",
        "shell.rs",
        "web.rs",
    ],
    compile_data = ["shell.html"],
    crate_name = "lrb_monofile",
    edition = "2024",
    visibility = ["//visibility:public"],
    # keep: js-sys/wasm-bindgen/web-sys back `web.rs`, which is behind
    # `#[cfg(target_arch = "wasm32")]`. gazelle_rust runs in pure_bazel mode with
    # no module discovery, so it would add them unconditionally and break the
    # host `rust_test`.
    deps = [
        "@crates//:base64",
        "@crates//:flate2",
    ] + select({
        "@rules_rust//rust/platform:wasm32-unknown-unknown": [
            "@crates//:js-sys",
            "@crates//:wasm-bindgen",
            "@crates//:wasm-bindgen-futures",
            "@crates//:web-sys",
        ],
        "//conditions:default": [],
    }),
)

rust_test(
    name = "monofile_test",
    crate = ":monofile",
    edition = "2024",
)

# Browser coverage for the `window.__monofile` shim, which no rust_test can
# reach. Drives real Chrome because the bug class it guards against (IndexedDB
# schema versioning) needs a real IndexedDB. Skips when Chrome is absent.
py_test(
    name = "shim_test",
    srcs = ["shim_test.py"],
    data = ["shell.html"],
    env = {"MONOFILE_SHELL": "lrb/monofile/shell.html"},
)
