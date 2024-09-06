load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:pico.bzl", "pico_project")
load("//bzl/macros:python.bzl", "py_test")

py_library(
    name = "client",
    srcs = ["client.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//emb/network/node:dataclass_node",
        "//emb/network/serialize:cbor2_cobs",
        "//emb/network/transport:transporter",
    ],
)

py_binary(
    name = "shell",
    srcs = ["shell.py"],
    deps = [
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
        ":base_host",
    ],
    env = {
        "HOST_BIN": "$(rootpath :base_host)",
    },
    deps = [
        ":client",
        "//emb/network/transport:tcp",
    ],
)

cc_library(
    name = "base_cc",
    hdrs = ["base.hpp"],
    visibility = ["//visibility:public"],
    deps = [
        "//emb/network/node:node_cc",
        "//emb/network/serialize:cbor2_cobs_cc",
        "//emb/network/transport:serial_cc",
        "//emb/yaal:flash",
    ],
)

pico_project(
    name = "base",
    srcs = ["main.cc"],
    deps = [
        ":base_cc",
        "//emb/network/node:node_cc",
        "//emb/network/serialize:cbor2_cobs_cc",
        "//emb/network/transport:serial_cc",
    ],
)
