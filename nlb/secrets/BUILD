load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@rules_go//go:def.bzl", "go_binary", "go_library")
load("//bzl/macros:go_image.bzl", "go_image")

py_library(
    name = "secrets",
    srcs = ["secrets.py"],
    visibility = ["//visibility:public"],
)

go_binary(
    name = "spirit_tracks_bin",
    srcs = ["spirit_tracks.go"],
    visibility = ["//visibility:public"],
    deps = ["@com_github_tailscale_setec//client/setec"],
)

go_library(
    name = "secrets_lib",
    srcs = ["spirit_tracks.go"],
    importpath = "nlb/nlb/secrets",
    visibility = ["//visibility:private"],
    deps = ["@com_github_tailscale_setec//client/setec"],
)

go_image(
    name = "spirit_tracks",
    args = [],
    binary = ":spirit_tracks_bin",
    labels = ":labels.txt",
    local_tags = ["ghcr.io/ryandraves/spirit_tracks:latest"],
    platform_names = [
        ("arm64", "//bzl/platforms:linux_arm64"),
        ("amd64", "//bzl/platforms:linux_amd64"),
    ],
    remote_repo = "ghcr.io/ryandraves",
    remote_tags = [
        "latest",
    ],
    # Too big for CI
    tags = ["manual"],
)
