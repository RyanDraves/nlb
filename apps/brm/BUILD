# Bomberman ("brm") — a small Rust game built on macroquad with an authoritative
# headless server. See README.md for architecture and run instructions.
#
# Cargo manifests/lockfile are consumed by the `brm_crates` crate_universe hub
# declared in //:MODULE.bazel.
load("@aspect_bazel_lib//lib:copy_to_directory.bzl", "copy_to_directory")
load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_filegroup")

exports_files([
    "Cargo.toml",
    "Cargo.lock",
])

# Build the client for wasm32 (the rest of the bundle builds for the host).
platform_transition_filegroup(
    name = "client_wasm_for_web",
    srcs = ["//apps/brm/client:client_wasm"],
    tags = ["manual"],
    target_platform = "@rules_rust//rust/platform:wasm",
)

# The static site the server serves to browser/phone guests: index.html, the
# vendored macroquad + quad-net JS loaders, and the wasm client — flattened to
# the bundle root so they sit next to each other.
copy_to_directory(
    name = "web_bundle",
    srcs = [
        ":client_wasm_for_web",
        "//apps/brm/web:assets",
    ],
    root_paths = [
        "apps/brm/web",
        "apps/brm/client",
    ],
    tags = ["manual"],
    visibility = ["//visibility:public"],
)

# One-command launcher: `bazel run //apps/brm:serve`.
sh_binary(
    name = "serve",
    srcs = ["serve.sh"],
    data = [
        ":web_bundle",
        "//apps/brm/server",
    ],
    tags = ["manual"],
)
