load("//bzl/macros:python.bzl", "py_binary")

py_binary(
    name = "nlb_gh_feature",
    srcs = ["nlb_gh_feature.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//nlb/util:console_utils",
        "@pip//inquirerpy",
        "@pip//rich_click",
    ],
)
