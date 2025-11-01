load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_binary")

py_library(
    name = "client",
    srcs = ["client.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//nlb/util:secrets",
        "@pip//requests",
    ],
)

py_binary(
    name = "nlb_invite",
    srcs = ["nlb_invite.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":client",
        "//nlb/util:console_utils",
        "@pip//inquirerpy",
        "@pip//rich_click",
    ],
)
