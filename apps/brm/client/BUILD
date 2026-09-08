load("@rules_rust//rust:defs.bzl", "rust_binary")

# `mod gamepad;` carries a `#[cfg(not(target_arch = "wasm32"))]`; pure_bazel mode
# does no module discovery, so gazelle tries to resolve it as an external crate
# and warns on every run. It is a sibling source file, already in srcs below.
# gazelle:rust_ignore_import gamepad

# Native client for couch players (split-keyboard, controllers). macroquad/
# miniquad declare the platform GL/windowing frameworks they link via in-crate
# `#[link]` attributes, so no extra linkopts are needed here.
rust_binary(
    name = "client",
    srcs = [
        "audio.rs",
        "gamepad.rs",
        "input.rs",
        "main.rs",
        "net.rs",
        "render.rs",
        "touch.rs",
        "web.rs",
    ],
    compile_data = [
        "//apps/brm/assets:powerups.png",
        "//apps/brm/assets:sfx",
    ],
    edition = "2024",
    tags = ["manual"],
    visibility = ["//visibility:public"],
    # keep: ws/gilrs are behind `#[cfg(not(target_arch = "wasm32"))]`.
    # pure_bazel mode does no module discovery, so gazelle reads the cfgs
    # backwards here — it would drop ws from the native client and add
    # native-only gilrs to the wasm one.
    deps = [
        "//apps/brm/shared:brm_shared",
        "@crates//:bincode",
        "@crates//:gilrs",
        "@crates//:macroquad",
        "@crates//:serde",
        "@crates//:ws",
    ],
)

# Browser/phone client: same source compiled to a wasm32 binary. macroquad's
# wasm uses its own JS loader (mq_js_bundle.js, NOT wasm-bindgen) and calls the
# module's exported `main`, which only exists when built as a bin (a cdylib
# wouldn't export it). Build with `--platforms=@rules_rust//rust/platform:wasm`.
rust_binary(
    name = "client_wasm",
    srcs = [
        "audio.rs",
        "gamepad.rs",
        "input.rs",
        "main.rs",
        "net.rs",
        "render.rs",
        "touch.rs",
        "web.rs",
    ],
    compile_data = [
        "//apps/brm/assets:powerups.png",
        "//apps/brm/assets:sfx",
    ],
    crate_name = "brm_client",
    edition = "2024",
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
    # keep: ws/gilrs are behind `#[cfg(not(target_arch = "wasm32"))]`.
    # pure_bazel mode does no module discovery, so gazelle reads the cfgs
    # backwards here — it would drop ws from the native client and add
    # native-only gilrs to the wasm one.
    deps = [
        "//apps/brm/shared:brm_shared",
        "@crates//:bincode",
        "@crates//:macroquad",
        "@crates//:serde",
    ],
)
