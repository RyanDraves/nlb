load("@aspect_bazel_lib//:bzl_library.bzl", "bzl_library")
load("//bzl/macros:python.bzl", "py_binary")

package(default_visibility = ["//visibility:public"])

exports_files([
    "pytest_wrapper.py",
    "cc_alias.hpp.template",
])

bzl_library(
    name = "buffham",
    srcs = ["buffham.bzl"],
    deps = [
        "@aspect_bazel_lib//lib:write_source_files",
        "@aspect_rules_py//py:defs",
        "@rules_cc//cc:defs_bzl",
    ],
)

bzl_library(
    name = "cc",
    srcs = ["cc.bzl"],
    deps = [
        "@aspect_bazel_lib//lib:transitions",
        "@bazel_skylib//rules:expand_template",
        "@rules_cc//cc:defs_bzl",
    ],
)

bzl_library(
    name = "emb",
    srcs = ["emb.bzl"],
    deps = [
        ":python",
    ],
)

# //bzl/rules:platform_transition needs a fix in rules_cc
# bzl_library(
#     name = "js_image",
#     srcs = ["js_image.bzl"],
#     deps = [
#         "//bzl/rules:platform_transition",
#         "@aspect_rules_js//js:defs",
#         "@rules_oci//oci:defs",
#     ],
# )

bzl_library(
    name = "next",
    srcs = ["next.bzl"],
    deps = [
        "@aspect_rules_js//js:defs",
    ],
)

bzl_library(
    name = "patch",
    srcs = ["patch.bzl"],
    deps = [],
)

# Waiting for rules_pico to support bzl_library
# https://github.com/raspberrypi/pico-sdk/pull/2674
# bzl_library(
#     name = "pico",
#     srcs = ["pico.bzl"],
#     deps = [
#         "//bzl/macros:emb",
#         "//bzl/rules:pico",
#         "@aspect_bazel_lib//lib:transitions",
#         "@pico-sdk//bazel/toolchain:objcopy",
#         "@rules_cc//cc:defs_bzl",
#     ],
# )

bzl_library(
    name = "python",
    srcs = ["python.bzl"],
    deps = [
        "@aspect_rules_py//py:defs",
        "@pip//:requirements.bzl",
        "@rules_python//python:pip_bzl",
    ],
)

py_binary(
    name = "pytest_wrapper",
    srcs = ["pytest_wrapper.py"],
    add_completions = False,
    visibility = ["//visibility:public"],
    deps = ["@pip//pytest"],
)

bzl_library(
    name = "go_image",
    srcs = ["go_image.bzl"],
    deps = [
        "@aspect_bazel_lib//lib:transitions",
        "@rules_oci//oci:defs",
        "@tar.bzl//tar:tar",
    ],
)

# Starlark Gazelle extension is too primitive to accept other directives
# gazelle:ignore
