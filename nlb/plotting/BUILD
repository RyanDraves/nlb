load("@aspect_rules_py//py:defs.bzl", "py_library")

py_library(
    name = "daltonize",
    srcs = ["daltonize.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//daltonize",
        "@pip//matplotlib",
        "@pip//numpy",
        "@pip//pillow",
        "@pip//setuptools",
    ],
)

py_library(
    name = "palette",
    srcs = ["palette.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//cycler",
        "@pip//matplotlib",
        "@pip//numpy",
    ],
)
