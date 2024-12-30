load("@crates//:defs.bzl", "aliases", "all_crate_deps")
load("@rules_rust//rust:defs.bzl", "rust_shared_library")
load("@rules_rust//wasm_bindgen:defs.bzl", "rust_wasm_bindgen")

# TODO: Consider using some rustc flags
# https://github.com/manekinekko/catsify/blob/90eda4d5440e542f6b1ebf1d26d6b2add1de48a0/api/rust/BUILD.bazel#L20-L26
rust_shared_library(
    name = "game_of_life_so",
    srcs = [
        "lib.rs",
        "utils.rs",
    ],
    aliases = aliases(),
    proc_macro_deps = all_crate_deps(
        proc_macro = True,
    ),
    target_compatible_with = [
        "@platforms//cpu:wasm32",
    ],
    deps = all_crate_deps(
        normal = True,
    ),
)

rust_wasm_bindgen(
    name = "game_of_life",
    target = "bundler",
    target_arch = "wasm32",
    visibility = ["//visibility:public"],
    wasm_file = ":game_of_life_so",
)
