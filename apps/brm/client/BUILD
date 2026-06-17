load("@rules_rust//rust:defs.bzl", "rust_binary")

exports_files(["Cargo.toml"])

# Native client for couch players (split-keyboard, controllers). macroquad/
# miniquad declare the platform GL/windowing frameworks they link via in-crate
# `#[link]` attributes, so no extra linkopts are needed here.
rust_binary(
    name = "client",
    srcs = glob(["src/*.rs"]),
    compile_data = ["//apps/brm/assets:powerups.png"],
    edition = "2021",
    tags = ["manual"],
    visibility = ["//visibility:public"],
    deps = [
        "//apps/brm/shared:brm_shared",
        "@brm_crates//:bincode",
        "@brm_crates//:gilrs",
        "@brm_crates//:macroquad",
        "@brm_crates//:serde",
        "@brm_crates//:ws",
    ],
)

# Browser/phone client: same source compiled to a wasm32 binary. macroquad's
# wasm uses its own JS loader (mq_js_bundle.js, NOT wasm-bindgen) and calls the
# module's exported `main`, which only exists when built as a bin (a cdylib
# wouldn't export it). Build with `--platforms=@rules_rust//rust/platform:wasm`.
rust_binary(
    name = "client_wasm",
    srcs = glob(["src/*.rs"]),
    compile_data = ["//apps/brm/assets:powerups.png"],
    crate_name = "brm_client",
    edition = "2021",
    rustc_flags = [
        "--codegen=opt-level=z",
        # macroquad/miniquad's JS-provided functions (ws_connect, init_webgl, …)
        # are undefined at link time; tell wasm-ld to turn undefined symbols into
        # wasm imports (resolved by the JS loader at runtime) instead of erroring.
        "-Clink-arg=--allow-undefined",
    ],
    tags = ["manual"],
    target_compatible_with = ["@platforms//cpu:wasm32"],
    visibility = ["//visibility:public"],
    deps = [
        "//apps/brm/shared:brm_shared",
        "@brm_crates//:bincode",
        "@brm_crates//:macroquad",
        "@brm_crates//:serde",
    ],
)

