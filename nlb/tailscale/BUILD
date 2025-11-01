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
