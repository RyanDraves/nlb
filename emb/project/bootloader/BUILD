load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_cc_library", "buffham_py_library")
load("//bzl/macros:pico.bzl", "pico_project")

buffham(
    name = "bootloader_bh",
    srcs = ["bootloader.bh"],
)

buffham_py_library(
    name = "bootloader_bh_py",
    bh = ":bootloader_bh",
)

buffham_cc_library(
    name = "bootloader_bh_cc",
    bh = ":bootloader_bh",
)

pico_project(
    name = "bootloader_pico",
    srcs = ["main.cc"],
    deps = [
        ":bootloader_bh_cc",
        "//emb/network/serialize:bh_cobs_cc",
        "//emb/network/transport:serial_cc",
        "//emb/project/base:base_bh_cc",
        "//emb/yaal:flash",
        "@pico-sdk//src/rp2_common/pico_stdlib",
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
