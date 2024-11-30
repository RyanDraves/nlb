load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_cc_library", "buffham_py_library")
load("//bzl/macros:emb.bzl", "host_test")
load("//bzl/macros:pico.bzl", "pico_project")

py_library(
    name = "client",
    srcs = ["client.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":robo24_bh_py",
        "//emb/project:client",
        "//emb/project/base:base_bh_py",
        "//emb/project/base:client",
        "//nlb/buffham:bh",
    ],
)

buffham(
    name = "robo24_bh",
    srcs = ["robo24.bh"],
)

buffham_py_library(
    name = "robo24_bh_py",
    bh = ":robo24_bh",
    # Current limitation of Buffham that this needs to be spelled out
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
        "//emb/slic:hc_sr04",
        "//emb/yaal:gpio",
        "//emb/yaal:timer",
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
        "//emb/util:log",
    ],
)

host_test(
    name = "host_test",
    srcs = ["host_test.py"],
    binary = ":robo24",
    deps = [
        ":client",
        ":robo24_bh_py",
        "//emb/project:host_test_base",
    ],
)

py_binary(
    name = "shell",
    srcs = ["shell.py"],
    deps = [
        ":client",
        ":robo24_bh_py",
        "//emb/project:shell",
    ],
)
