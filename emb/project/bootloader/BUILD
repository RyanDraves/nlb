load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_cc_library", "buffham_py_library")
load("//bzl/macros:pico.bzl", "pico_project")

buffham(
    name = "bootloader",
    srcs = ["bootloader.bh"],
)

buffham_py_library(
    name = "bootloader_bh_py",
    bh = ":bootloader",
)

buffham_cc_library(
    name = "bootloader_bh_cc",
    bh = ":bootloader",
)

pico_project(
    name = "bootloader_pico",
    srcs = ["main.cc"],
    include_host = False,
    deps = [
        ":bootloader_bh_cc",
        "//emb/network/serialize:bh_cobs_cc",
        "//emb/network/transport:serial_cc",
        "//emb/project/base:base_bh_cc",
        "//emb/yaal:flash",
    ],
)

py_binary(
    name = "shell",
    srcs = ["shell.py"],
    deps = [
        "//emb/network/transport:usb",
        "//emb/project/base:base_bh_py",
    ],
)
