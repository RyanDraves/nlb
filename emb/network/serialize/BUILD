load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_cc_library", "buffham_py_library")
load("//bzl/macros:python.bzl", "py_test")
load("//bzl/macros:unittest.bzl", "cc_unittest")

py_library(
    name = "bh_cobs",
    srcs = ["bh_cobs.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//emb/network/frame:cobs_lib",
        "//nlb/buffham:bh",
    ],
)

py_test(
    name = "bh_cobs_test",
    srcs = ["bh_cobs_test.py"],
    deps = [
        ":bh_cobs",
        ":testdata/test_bh_py",
    ],
)

cc_library(
    name = "bh_cobs_cc",
    srcs = ["bh_cobs.cc"],
    hdrs = ["bh_cobs.hpp"],
    visibility = ["//visibility:public"],
    deps = [
        ":serializer_cc",
        "//emb/network/frame:cobs_cc",
    ],
)

cc_unittest(
    name = "bh_cobs_cc_test",
    srcs = ["bh_cobs_test.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":bh_cobs_cc",
        ":testdata/test_bh_cc",
    ],
)

py_library(
    name = "serializer",
    srcs = ["serializer.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//nlb/util:dataclass",
    ],
)

cc_library(
    name = "serializer_cc",
    hdrs = ["serializer.hpp"],
    visibility = ["//visibility:public"],
)

buffham(
    name = "testdata/test_bh",
    srcs = ["testdata/test.bh"],
)

buffham_py_library(
    name = "testdata/test_bh_py",
    bh = ":testdata/test_bh",
)

buffham_cc_library(
    name = "testdata/test_bh_cc",
    bh = ":testdata/test_bh",
)
