load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@rules_cc//cc:defs.bzl", "cc_library")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_py_write")
load("//bzl/macros:cc.bzl", "cc_unittest")
load("//bzl/macros:emb.bzl", "host_test", "wav_cc_library")
load("//bzl/macros:pico.bzl", "pico_project")
load("//bzl/macros:python.bzl", "py_binary", "py_test")

py_library(
    name = "client",
    srcs = ["client.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//emb/project:client",
        "//emb/project/base:base_bh_py",
        "//emb/project/base:client",
        "//emb/project/punbox:punbox_bh_py",
        "//nlb/buffham:bh",
    ],
)

buffham(
    name = "punbox_bh",
    src = "punbox.bh",
    cc = True,
    py = True,
    deps = [
        "//emb/project/base:base_bh",
    ],
)

buffham_py_write(
    name = "punbox_bh_py_write",
)

wav_cc_library(
    name = "rimshot",
    namespace = "emb::project::punbox",
    symbol = "rimshot",
    wav = "data/rimshot.wav",
)

cc_library(
    name = "logic",
    srcs = ["logic.cc"],
    hdrs = ["logic.hpp"],
    deps = [
        "//emb/yaal:audio",
        "//emb/yaal:audio_clip",
        "//emb/yaal:gpio",
    ],
)

cc_unittest(
    name = "logic_test",
    srcs = ["logic_test.cc"],
    deps = [
        ":logic",
        "//emb/yaal:host_audio",
        "//emb/yaal:host_gpio",
    ],
)

cc_library(
    name = "punbox_cc",
    srcs = ["punbox.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":logic",
        ":punbox_bh_cc",
        ":rimshot",
        "//emb/project/base:base_bh_cc",
        "//emb/yaal:audio",
        "//emb/yaal:gpio",
        "//emb/yaal:timer",
    ],
)

pico_project(
    srcs = ["main.cc"],
    names = ["punbox_pico"],
    deps = [
        ":punbox_cc",
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
    binary = ":punbox",
    deps = [
        ":client",
        ":punbox_bh_py",
        "//emb/project:host_test_base",
    ],
)

# gazelle:python_ignore_files hil_test.py
py_test(
    name = "hil_test",
    srcs = ["hil_test.py"],
    # Requires a punbox board connected over USB; run manually
    tags = ["manual"],
    deps = [
        ":client",
        ":punbox_bh_py",
        "//emb/network/transport:usb",
    ],
)

py_binary(
    name = "shell",
    srcs = ["shell.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":client",
        "//emb/project:shell",
        "//emb/project/punbox:punbox_bh_py",
        "@pip//rich_click",
    ],
)
