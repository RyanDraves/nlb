load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:python.bzl", "py_test")
load("//bzl/macros:unittest.bzl", "cc_unittest")

py_library(
    name = "cbor2_cobs",
    srcs = ["cbor2_cobs.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("cbor2"),
        "//emb/network/frame:cobs_lib",
        "//nlb/util:dataclass",
    ],
)

py_test(
    name = "cbor2_cobs_test",
    srcs = ["cbor2_cobs_test.py"],
    deps = [
        ":cbor2_cobs",
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

cc_library(
    name = "cbor2_cobs_cc",
    srcs = ["cbor2_cobs.cc"],
    hdrs = ["cbor2_cobs.hpp"],
    visibility = ["//visibility:public"],
    deps = [
        ":serializer_cc",
        "//emb/network/frame:cobs_cc",
        "@reflect-cpp//:refl",
        "@tinycbor//:cbor",
    ],
)

cc_unittest(
    name = "cbor2_cobs_cc_test",
    srcs = ["cbor2_cobs_test.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":cbor2_cobs_cc",
    ],
)
