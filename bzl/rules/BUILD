load("@bazel_lib//:bzl_library.bzl", "bzl_library")

package(default_visibility = ["//visibility:public"])

bzl_library(
    name = "feature",
    srcs = ["feature.bzl"],
    deps = [
        "@bazel_skylib//rules:common_settings",
        "@rules_cc//cc:defs_bzl",
    ],
)

bzl_library(
    name = "pico",
    srcs = ["pico.bzl"],
    deps = [
    ],
)

# Waiting on a fix in rules_cc
# https://github.com/bazelbuild/rules_cc/pull/507
# bzl_library(
#     name = "platform_transition",
#     srcs = ["platform_transition.bzl"],
#     deps = [
#         "@rules_cc//cc/common",
#     ],
# )
