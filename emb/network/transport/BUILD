load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pico-sdk//bazel:pico_btstack_make_gatt_header.bzl", "pico_btstack_make_gatt_header")
load("@pip//:requirements.bzl", "requirement")
load("@rules_cc//cc:defs.bzl", "cc_library")
load("//bzl/macros:unittest.bzl", "cc_host_test", "cc_unittest")

py_library(
    name = "ble",
    srcs = ["ble.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("bleak"),
    ],
)

py_library(
    name = "usb",
    srcs = ["usb.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("pyserial"),
    ],
)

py_library(
    name = "transporter",
    srcs = ["transporter.py"],
    visibility = ["//visibility:public"],
    deps = [
    ],
)

py_library(
    name = "tcp",
    srcs = ["tcp.py"],
    visibility = ["//visibility:public"],
    deps = [requirement("pyzmq")],
)

pico_btstack_make_gatt_header(
    name = "nus",
    src = "nus.gatt",
)

cc_library(
    name = "btstack_config",
    hdrs = ["btstack_config.h"],
    includes = ["."],  # Shorten the include path to what dependents expect
    visibility = ["//visibility:public"],
)

cc_library(
    name = "transporter_cc",
    hdrs = ["transporter.hpp"],
    visibility = ["//visibility:public"],
)

alias(
    name = "transport",
    actual = select(
        {
            "//bzl/constraints:comms_protocol_ble_enabled": ":transport_ble",
            "//bzl/constraints:comms_protocol_serial_enabled": ":transport_serial",
            "//bzl/constraints:comms_protocol_zmq_enabled": ":transport_zmq",
            "//bzl/constraints:comms_protocol_unittest_enabled": ":transport_unittest",
        },
    ),
    visibility = ["//visibility:public"],
)

cc_library(
    name = "transport_ble",
    srcs = ["pico/ble.cc"],
    hdrs = ["transport.hpp"],
    # Keep this as generic as possible; let the alias handle flag-related constraints
    target_compatible_with = ["@platforms//cpu:armv6-m"],
    deps = [
        ":nus",
        "@pico-sdk//src/common/pico_sync",
        "@pico-sdk//src/rp2_common/pico_btstack",
        "@pico-sdk//src/rp2_common/pico_cyw43_arch",
        "@pico-sdk//src/rp2_common/pico_stdlib",
    ],
)

cc_library(
    name = "transport_serial",
    srcs = ["pico/serial.cc"],
    hdrs = ["transport.hpp"],
    target_compatible_with = ["@platforms//cpu:armv6-m"],
    deps = [
        "@pico-sdk//src/rp2_common/pico_cyw43_arch",
        "@pico-sdk//src/rp2_common/pico_stdlib",
    ],
)

cc_library(
    name = "transport_zmq",
    srcs = ["host/zmq.cc"],
    hdrs = ["transport.hpp"],
    deps = ["@cppzmq"],
)

cc_library(
    name = "transport_unittest",
    srcs = ["unittest/bent_pipe.cc"],
    hdrs = ["transport.hpp"],
    target_compatible_with = ["//bzl/constraints:unittest"],
    deps = [
        ":transporter_cc",
    ],
)

cc_unittest(
    name = "bent_pipe_test",
    srcs = ["unittest/bent_pipe_test.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":transport_unittest",
    ],
)

cc_host_test(
    name = "zmq_test",
    srcs = ["host/zmq_test.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":transport_zmq",
        "@cppzmq",
    ],
)
