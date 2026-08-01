# iir ("is it raining?") — axum server + Leptos wasm client. See README.md.
# Cargo manifests/lockfile are consumed by the `iir_crates` crate_universe hub
# declared in //:MODULE.bazel.
load("@aspect_bazel_lib//lib:copy_to_directory.bzl", "copy_to_directory")
load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_filegroup")
load("@rules_shell//shell:sh_binary.bzl", "sh_binary")
load("@tar.bzl//tar:mtree.bzl", "mutate")
load("@tar.bzl//tar:tar.bzl", "tar")
load("//bzl/macros:rust_image.bzl", "rust_image")

exports_files([
    "Cargo.toml",
    "Cargo.lock",
])

# Build the wasm-bindgen'd client for wasm32 (the rest builds for the host).
platform_transition_filegroup(
    name = "client_wasm_for_web",
    srcs = ["//apps/iir/client:iir_client"],
    tags = ["manual"],
    target_platform = "@rules_rust//rust/platform:wasm",
)

# The static site the server serves: index.html + CSS + favicon + the ES-module
# wasm client, flattened to the bundle root so they sit next to each other.
copy_to_directory(
    name = "web_bundle",
    srcs = [
        ":client_wasm_for_web",
        "//apps/iir/web:assets",
    ],
    root_paths = [
        "apps/iir/web",
        # rust_wasm_bindgen nests its outputs under a dir named after the target.
        "apps/iir/client/iir_client",
    ],
    tags = ["manual"],
    visibility = ["//visibility:public"],
)

# One-command launcher: `bazel run //apps/iir:serve`.
sh_binary(
    name = "serve",
    srcs = ["serve.sh"],
    data = [
        ":web_bundle",
        "//apps/iir/server",
    ],
    tags = ["manual"],
)

# The web bundle as an image layer under /opt/web (IIR_WEB_DIR points here).
tar(
    name = "web_layer",
    srcs = [":web_bundle"],
    mutate = mutate(
        package_dir = "opt/web",
        strip_prefix = "apps/iir/web_bundle",
    ),
    tags = ["manual"],
)

# Container image for the server + embedded web client. Cross-compiled to
# Linux via the hermetic Zig toolchains (platform transition):
#   bazel run //apps/iir:iir_amd64_load   # build & load locally
#   bazel run //apps/iir:iir_push         # push multi-arch (login first)
rust_image(
    name = "iir",
    additional_tars = [":web_layer"],
    binary = "//apps/iir/server",
    env = {
        "IIR_WEB_DIR": "/opt/web",
        "IIR_PORT": "3000",
        # Secret file, mounted by services/iir/docker-compose.yaml (whose own
        # `environment:` also sets this, overriding the default at runtime).
        "OPENWEATHER_API_KEY_FILE": "/secrets/iir_openweathermap_api_key",
    },
    exposed_ports = ["3000/tcp"],
    labels = ":labels.txt",
    local_tags = ["ghcr.io/ryandraves/iir:latest"],
    platform_names = [
        ("arm64", "//bzl/platforms:linux_arm64"),
        ("amd64", "//bzl/platforms:linux_amd64"),
    ],
    remote_repo = "ghcr.io/ryandraves",
    remote_tags = ["latest"],
    # Too big for CI; built and pushed manually.
    tags = ["manual"],
)
