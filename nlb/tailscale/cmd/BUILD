load("@rules_go//go:def.bzl", "go_binary", "go_library")

go_binary(
    name = "main",
    embed = [":cmd_lib"],
    visibility = ["//visibility:public"],
)

go_library(
    name = "cmd_lib",
    srcs = ["main.go"],
    importpath = "nlb/nlb/tailscale/cmd",
    visibility = ["//visibility:private"],
    deps = [
        "//nlb/tailscale",
        "@com_github_spf13_cobra//:cobra",
    ],
)
