load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:python.bzl", "py_test")

py_library(
    name = "progress_bar",
    srcs = ["progress_bar.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("requests"),
        requirement("rich"),
    ],
)

py_test(
    name = "progress_bar_test",
    srcs = ["progress_bar_test.py"],
    deps = [
        ":progress_bar",
        requirement("responses"),
    ],
)
