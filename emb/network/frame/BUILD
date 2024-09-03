load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pybind11_bazel//:build_defs.bzl", "pybind_extension")
load("//bzl/macros:python.bzl", "py_test")
load("//bzl/macros:unittest.bzl", "cc_unittest")

cc_library(
    name = "cobs_cc",
    srcs = ["cobs.cc"],
    hdrs = ["cobs.hpp"],
    visibility = ["//visibility:public"],
)

cc_unittest(
    name = "cobs_test_cc",
    srcs = ["cobs_test.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":cobs_cc",
    ],
)

pybind_extension(
    name = "cobs",
    srcs = ["bindings.cc"],
    deps = [
        ":cobs_cc",
    ],
)

py_library(
    name = "cobs_lib",
    data = [":cobs.so"],
    imports = ["."],
)

py_test(
    name = "cobs_test",
    srcs = ["cobs_test.py"],
    deps = [
        ":cobs_lib",
    ],
)
