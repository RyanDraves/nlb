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
        ":robo24_bh_py",
        requirement("rich"),
    ],
)

buffham(
    name = "robo24_bh",
    srcs = ["robo24.bh"],
)

buffham_py_library(
    name = "robo24_bh_py",
    bh = ":robo24_bh",
    bh_deps = [
        "//emb/project/base:base_bh",
    ],
    deps = [
        "//emb/project/base:base_bh_py",
    ],
)

buffham_cc_library(
    name = "robo24_bh_cc",
    bh = ":robo24_bh",
    bh_deps = [
        "//emb/project/base:base_bh",
    ],
    deps = [
        "//emb/project/base:base_bh_cc",
    ],
)

cc_library(
    name = "robo24_cc",
    srcs = ["robo24.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":robo24_bh_cc",
        "//emb/project/base:base_bh_cc",
    ],
)

pico_project(
    name = "robo24_pico",
    srcs = ["main.cc"],
    deps = [
        ":robo24_cc",
        "//emb/network/node:node_cc",
        "//emb/network/serialize:bh_cobs_cc",
        "//emb/network/transport:serial_cc",
        "//emb/project/base:base_cc",
    ],
)

py_test(
    name = "host_test",
    srcs = ["host_test.py"],
    data = [
        ":robo24",
    ],
    env = {
        "HOST_BIN": "$(rootpath :robo24)",
    },
    deps = [
        ":client",
        ":robo24_bh_py",
        "//emb/network/transport:tcp",
        "//emb/project/bootloader:bootloader_bh_py",
    ],
)

py_binary(
    name = "shell",
    srcs = ["shell.py"],
    deps = [
        ":client",
        ":robo24_bh_py",
        "//emb/network/transport:tcp",
        "//emb/network/transport:usb",
        "//nlb/util:click_utils",
        requirement("rich-click"),
        requirement("IPython"),
    ],
)
