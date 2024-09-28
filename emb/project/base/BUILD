load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_cc_library", "buffham_py_library")
load("//bzl/macros:pico.bzl", "pico_project")
load("//bzl/macros:python.bzl", "py_test")

# Necessary consequency to make `bzl/macros/emb.bzl` work (simply)
exports_files(["flash.py"])

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
    name = "base_bh",
    srcs = ["base.bh"],
)

buffham_py_library(
    name = "base_bh_py",
    bh = ":base_bh",
)

buffham_cc_library(
    name = "base_bh_cc",
    bh = ":base_bh",
)

cc_library(
    name = "base_cc",
    srcs = ["base.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":base_bh_cc",
        "//emb/project/bootloader:bootloader_bh_cc",
        "//emb/yaal:flash",
        "//emb/yaal:watchdog",
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

py_binary(
    name = "flash",
    srcs = ["flash.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":base_bh_py",
        ":client",
        "//emb/network/transport:tcp",
        "//emb/network/transport:usb",
        "//nlb/util:click_utils",
        requirement("rich-click"),
    ],
)

py_test(
    name = "host_test",
    srcs = ["host_test.py"],
    data = [
        ":base",
    ],
    env = {
        "HOST_BIN": "$(rootpath :base)",
    },
    deps = [
        ":base_bh_py",
        ":client",
        "//emb/network/transport:tcp",
        "//emb/project/bootloader:bootloader_bh_py",
    ],
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
