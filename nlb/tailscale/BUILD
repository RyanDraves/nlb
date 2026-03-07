load("@rules_go//go:def.bzl", "go_library", "go_test")
load("//bzl/macros:python.bzl", "py_binary")

py_binary(
    name = "nlb_tailscale",
    srcs = ["nlb_tailscale.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//nlb/util:console_utils",
        "//nlb/util:prompt_utils",
        "@pip//inquirerpy",
        "@pip//rich_click",
    ],
)

go_library(
    name = "tailscale",
    srcs = ["tailscale.go"],
    importpath = "nlb/nlb/tailscale",
    visibility = ["__subpackages__"],
    deps = [
        "//nlb/util",
        "@com_tailscale//client/local",
        "@com_tailscale//client/tailscale/apitype",
        "@com_tailscale//ipn/ipnstate",
        "@com_tailscale//tailcfg",
    ],
)

go_test(
    name = "tailscale_test",
    srcs = ["tailscale_test.go"],
    embed = [":tailscale"],
    deps = [
        "@com_tailscale//client/tailscale/apitype",
        "@com_tailscale//ipn/ipnstate",
        "@com_tailscale//tailcfg",
        "@com_tailscale//types/key",
    ],
)
