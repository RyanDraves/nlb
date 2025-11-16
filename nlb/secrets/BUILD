load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@rules_go//go:def.bzl", "go_binary", "go_library")

py_library(
    name = "secrets",
    srcs = ["secrets.py"],
    visibility = ["//visibility:public"],
)

go_binary(
    name = "spirit_tracks",
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
