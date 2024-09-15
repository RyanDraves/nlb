load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_cc_library", "buffham_py_library")
load("//bzl/macros:pico.bzl", "pico_project")
load("//bzl/macros:python.bzl", "py_test")

py_library(
    name = "client",
    srcs = ["client.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":base_bh_py",
        "//emb/project/bootloader:bootloader_bh_py",
        requirement("rich"),
    ],
)

buffham(
    name = "base",
    srcs = ["base.bh"],
)

buffham_py_library(
    name = "base_bh_py",
    bh = ":base",
)

buffham_cc_library(
    name = "base_bh_cc",
    bh = ":base",
)

py_binary(
    name = "shell",
    srcs = ["shell.py"],
    deps = [
        ":base_bh_py",
        ":client",
        "//emb/network/transport:tcp",
        "//emb/network/transport:usb",
        "//nlb/util:click_utils",
        requirement("rich-click"),
        requirement("IPython"),
    ],
)

py_test(
    name = "host_test",
    srcs = ["host_test.py"],
    data = [
        ":base_host",
    ],
    env = {
        "HOST_BIN": "$(rootpath :base_host)",
    },
    deps = [
        ":base_bh_py",
        ":client",
        "//emb/network/transport:tcp",
        "//emb/project/bootloader:bootloader_bh_py",
    ],
)

cc_library(
    name = "base_cc",
    srcs = ["base.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":base_bh_cc",
        "//emb/project/bootloader:bootloader_bh_cc",
        "//emb/yaal:flash",
    ],
)

pico_project(
    name = "base_pico",
    srcs = ["main.cc"],
    deps = [
        ":base_cc",
        "//emb/network/node:node_cc",
        "//emb/network/serialize:bh_cobs_cc",
        "//emb/network/transport:serial_cc",
    ],
)
