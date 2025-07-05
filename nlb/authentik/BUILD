load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:python.bzl", "py_binary")

py_library(
    name = "client",
    srcs = ["client.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("requests"),
        "//nlb/util:secrets",
    ],
)

py_binary(
    name = "nlb_invite",
    srcs = ["nlb_invite.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("inquirerpy"),
        requirement("rich-click"),
        ":client",
        "//nlb/util:console_utils",
    ],
)
