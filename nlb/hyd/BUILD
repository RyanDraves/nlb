load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_test")

py_library(
    name = "progress_bar",
    srcs = ["progress_bar.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//requests",
        "@pip//rich",
    ],
)

py_test(
    name = "progress_bar_test",
    srcs = ["progress_bar_test.py"],
    deps = [
        ":progress_bar",
        "@pip//requests",
        "@pip//responses",
    ],
)
