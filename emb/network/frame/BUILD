load("@aspect_rules_py//py:defs.bzl", "py_library")
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

###
# Copied from https://github.com/psigen/bazel-python-cpp-example/blob/281d520ce456f6f41bd1f042401594693a98a5d7/binding/BUILD.bazel
# (including the comment that this was adapted from a Github issue)
###

# Adapted from: https://github.com/bazelbuild/bazel/issues/1475
cc_binary(
    name = "cobs.so",
    srcs = ["bindings.cc"],
    linkshared = 1,
    visibility = ["//visibility:public"],
    deps = [
        ":cobs_cc",
        "@pybind11",
    ],
)

py_library(
    name = "cobs",
    data = [":cobs.so"],
    visibility = ["//visibility:public"],
)

###
# End copy pasta
###

py_test(
    name = "cobs_test",
    srcs = ["cobs_test.py"],
    deps = [
        ":cobs",
    ],
)
