load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@rules_cc//cc:defs.bzl", "cc_library")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_py_write")
load("//bzl/macros:emb.bzl", "host_test")
load("//bzl/macros:pico.bzl", "pico_project")
load("//bzl/macros:python.bzl", "py_binary")

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
    src = "robo24.bh",
    cc = True,
    py = True,
    deps = [
        "//emb/project/base:base_bh",
    ],
)

buffham_py_write(
    name = "robo24_bh_py_write",
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
    srcs = ["main.cc"],
    names = ["robo24_pico"],
    deps = [
        ":robo24_cc",
        "//emb/network/node:node_cc",
        "//emb/network/serialize:bh_cobs_cc",
        "//emb/network/transport:comms_transport",
        "//emb/network/transport:log_transport",
        "//emb/project/base:base_cc",
        "//emb/util:log",
    ],
)

# gazelle:python_ignore_files host_test.py
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
    visibility = ["//:__subpackages__"],
    deps = [
        ":client",
        ":robo24_bh_py",
        "//emb/project:shell",
        "@pip//rich_click",
    ],
)
