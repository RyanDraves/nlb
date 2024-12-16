load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@bazel_skylib//rules:common_settings.bzl", "bool_flag")
load("@pip//:requirements.bzl", "requirement")
load("@rules_cc//cc:defs.bzl", "cc_library")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_py_write")
load("//bzl/macros:emb.bzl", "host_test")
load("//bzl/macros:pico.bzl", "pico_project")
load("//bzl/rules:feature.bzl", "feature_cc_library")

# Necessary consequency to make `bzl/macros/emb.bzl` work (simply)
exports_files(["flash.py"])

py_library(
    name = "client",
    srcs = ["client.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":base_bh_py",
        "//emb/project:client",
        "//emb/project/bootloader:bootloader_bh_py",
        "//nlb/buffham:bh",
        requirement("rich"),
    ],
)

buffham(
    name = "base_bh",
    src = "base.bh",
    cc = True,
    py = True,
    visibility = ["//visibility:public"],
)

buffham_py_write(
    name = "base_bh_py_write",
)

# TODO: Make this a generic flag for all Pico_W specifics?
bool_flag(
    name = "pio_blink",
    build_setting_default = False,
)

feature_cc_library(
    name = "pio_blink_cc",
    build_setting = ":pio_blink",
)

cc_library(
    name = "base_cc",
    srcs = ["base.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":base_bh_cc",
        ":pio_blink_cc",
        "//emb/project/bootloader:bootloader_bh_cc",
        "//emb/util:log",
        "//emb/yaal:flash",
        "//emb/yaal:pio_blink",
        "//emb/yaal:watchdog",
    ],
)

pico_project(
    name = "base_pico",
    srcs = ["main.cc"],
    visibility = [
        ":__subpackages__",
        "//emb/project/bootloader:__pkg__",
    ],
    deps = [
        ":base_cc",
        "//emb/network/node:node_cc",
        "//emb/network/serialize:bh_cobs_cc",
        "//emb/network/transport:serial_cc",
        "//emb/util:log",
    ],
)

# TODO: Just make `pico_project` accept multiple platforms or more
# flexibly pick the transport layer that it's compiled against.
pico_project(
    name = "base_pico_w",
    srcs = ["main.cc"],
    platform = "//bzl/platforms:rp2040_w",
    visibility = [
        ":__subpackages__",
        "//emb/project/bootloader:__pkg__",
    ],
    deps = [
        ":base_cc",
        "//emb/network/node:node_cc",
        "//emb/network/serialize:bh_cobs_cc",
        "//emb/network/transport:ble_cc",
        "//emb/network/transport:serial_cc",
        "//emb/util:log",
    ],
)

py_library(
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
        requirement("IPython"),
    ],
)

host_test(
    name = "host_test",
    srcs = ["host_test.py"],
    binary = ":base",
    deps = [
        ":base_bh_py",
        ":client",
        "//emb/project:host_test_base",
        "//emb/project/bootloader:bootloader_bh_py",
    ],
)

py_binary(
    name = "shell",
    srcs = ["shell.py"],
    deps = [
        ":base_bh_py",
        ":client",
        "//emb/project:shell",
        requirement("rich-click"),
    ],
)
