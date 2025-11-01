load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_test")

py_library(
    name = "bidirectional_dict",
    srcs = ["bidirectional_dict.py"],
    visibility = ["//visibility:public"],
)

py_test(
    name = "bidirectional_dict_test",
    srcs = ["bidirectional_dict_test.py"],
    deps = [
        ":bidirectional_dict",
    ],
)
