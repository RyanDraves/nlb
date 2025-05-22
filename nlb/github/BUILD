load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:python.bzl", "py_binary")

py_binary(
    name = "nlb_gh_feature",
    srcs = ["nlb_gh_feature.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("inquirerpy"),
        requirement("rich-click"),
        "//nlb/util:console_utils",
    ],
)
