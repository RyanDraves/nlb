load("@rules_cc//cc:defs.bzl", "cc_library")
load("//bzl/macros:cc.bzl", "cc_unittest")

cc_library(
    name = "log",
    hdrs = ["log.hpp"],
    visibility = ["//visibility:public"],
    deps = [
        "//emb/project/base:base_bh_cc",
    ],
)

cc_library(
    name = "ring_buffer",
    hdrs = ["ring_buffer.hpp"],
    visibility = ["//visibility:public"],
)

cc_unittest(
    name = "ring_buffer_test",
    srcs = ["ring_buffer_test.cc"],
    deps = [":ring_buffer"],
)
