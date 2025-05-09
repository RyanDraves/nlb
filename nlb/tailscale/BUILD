load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:python.bzl", "py_binary")

py_binary(
    name = "nlb_tailscale",
    srcs = ["nlb_tailscale.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("inquirerpy"),
        requirement("rich-click"),
        "//nlb/util:console_utils",
        "//nlb/util:prompt_utils",
    ],
)
