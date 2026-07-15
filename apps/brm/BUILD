# Bomberman ("brm") — a small Rust game built on macroquad with an authoritative
# headless server. See README.md for architecture and run instructions.
#
# Cargo manifests/lockfile are consumed by the `brm_crates` crate_universe hub
# declared in //:MODULE.bazel.
load("@aspect_bazel_lib//lib:copy_to_directory.bzl", "copy_to_directory")
load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_filegroup")
load("@tar.bzl//tar:mtree.bzl", "mutate")
load("@tar.bzl//tar:tar.bzl", "tar")
load("//bzl/macros:rust_image.bzl", "rust_image")

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

# The web bundle as an image layer under /opt/web (BRM_WEB_DIR points here).
tar(
    name = "web_layer",
    srcs = [":web_bundle"],
    mutate = mutate(
        package_dir = "opt/web",
        strip_prefix = "apps/brm/web_bundle",
    ),
    tags = ["manual"],
)

# Container image for the server + embedded web client. Cross-compiled to Linux
# via the hermetic Zig toolchains, so BUILD/RUN these with `--config=image`:
#   bazel run --config=image //apps/brm:brm_amd64_load   # build & load locally
#   bazel run --config=image //apps/brm:brm_push         # push multi-arch (login first)
rust_image(
    name = "brm",
    additional_tars = [":web_layer"],
    binary = "//apps/brm/server",
    env = {
        # Serve the web client from the layer above; bind all interfaces.
        "BRM_WEB_DIR": "/opt/web",
        "BRM_PORT": "8080",
    },
    exposed_ports = ["8080/tcp"],
    labels = ":labels.txt",
    local_tags = ["ghcr.io/ryandraves/brm:latest"],
    platform_names = [
        ("arm64", "//bzl/platforms:linux_arm64"),
        ("amd64", "//bzl/platforms:linux_amd64"),
    ],
    remote_repo = "ghcr.io/ryandraves",
    remote_tags = ["latest"],
    # Too big for CI; built and pushed manually.
    tags = ["manual"],
)
