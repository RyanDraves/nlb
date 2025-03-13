load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pico-sdk//bazel:pico_btstack_make_gatt_header.bzl", "pico_btstack_make_gatt_header")
load("@pip//:requirements.bzl", "requirement")
load("@rules_cc//cc:defs.bzl", "cc_library")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_py_write", "buffham_template")
load("//bzl/macros:cc.bzl", "cc_alias_library", "cc_host_test", "cc_unittest")

py_library(
    name = "ble",
    srcs = ["ble.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("bleak"),
        ":nus_bh_py",
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

buffham(
    name = "nus_bh",
    src = "nus.bh",
    py = True,
    visibility = ["//visibility:public"],
)

buffham_py_write(
    name = "nus_bh_py_write",
)

buffham_template(
    name = "nus_bh_gatt",
    bh = ":nus_bh",
    out_file = "nus.gatt",
    template = "nus_template.gatt",
)

pico_btstack_make_gatt_header(
    name = "nus",
    src = ":nus_bh_gatt",
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

# This library will automatically resolve to the transport layer picked by the
# `//bzl/configs:COMMS_PROTOCOL` flag
cc_alias_library(
    name = "comms_transport",
    alias_classname = "CommsTransport",
    include_and_classname = select(
        {
            "//bzl/constraints:comms_protocol_ble_enabled": {
                "{include_path}": "emb/network/transport/ble.hpp",
                "{dep_classname}": "Ble",
            },
            "//bzl/constraints:comms_protocol_serial_enabled": {
                "{include_path}": "emb/network/transport/serial.hpp",
                "{dep_classname}": "Serial",
            },
            "//bzl/constraints:comms_protocol_zmq_enabled": {
                "{include_path}": "emb/network/transport/zmq.hpp",
                "{dep_classname}": "Zmq",
            },
            "//bzl/constraints:comms_protocol_unittest_enabled": {
                "{include_path}": "emb/network/transport/bent_pipe.hpp",
                "{dep_classname}": "BentPipe",
            },
        },
    ),
    lib_select = select(
        {
            "//bzl/constraints:comms_protocol_ble_enabled": ":transport_ble",
            "//bzl/constraints:comms_protocol_serial_enabled": ":transport_serial",
            "//bzl/constraints:comms_protocol_zmq_enabled": ":transport_zmq",
            "//bzl/constraints:comms_protocol_unittest_enabled": ":transport_unittest",
        },
    ),
    visibility = ["//visibility:public"],
)

# This library will automatically resolve to the transport layer picked by the
# `//bzl/configs:LOG_PROTOCOL` flag
cc_alias_library(
    name = "log_transport",
    alias_classname = "LogTransport",
    include_and_classname = select(
        {
            "//bzl/constraints:log_protocol_ble_enabled": {
                "{include_path}": "emb/network/transport/ble.hpp",
                "{dep_classname}": "Ble",
            },
            "//bzl/constraints:log_protocol_serial_enabled": {
                "{include_path}": "emb/network/transport/serial.hpp",
                "{dep_classname}": "Serial",
            },
            "//bzl/constraints:log_protocol_zmq_enabled": {
                "{include_path}": "emb/network/transport/zmq.hpp",
                "{dep_classname}": "Zmq",
            },
            "//bzl/constraints:log_protocol_unittest_enabled": {
                "{include_path}": "emb/network/transport/bent_pipe.hpp",
                "{dep_classname}": "BentPipe",
            },
        },
    ),
    lib_select = select(
        {
            "//bzl/constraints:log_protocol_ble_enabled": ":transport_ble",
            "//bzl/constraints:log_protocol_serial_enabled": ":transport_serial",
            "//bzl/constraints:log_protocol_zmq_enabled": ":transport_zmq",
            "//bzl/constraints:log_protocol_unittest_enabled": ":transport_unittest",
        },
    ),
    visibility = ["//visibility:public"],
)

# These are the real libraries implementing the transport layers
cc_library(
    name = "transport_ble",
    srcs = ["pico/ble.cc"],
    hdrs = ["ble.hpp"],
    # Keep this as generic as possible; let the alias handle flag-related constraints
    target_compatible_with = ["@platforms//cpu:armv6-m"],
    deps = [
        ":nus",
        "//emb/util:log",
        "@pico-sdk//src/common/pico_sync",
        "@pico-sdk//src/rp2_common/pico_btstack",
        "@pico-sdk//src/rp2_common/pico_cyw43_arch",
    ],
)

cc_library(
    name = "transport_serial",
    srcs = ["pico/serial.cc"],
    hdrs = ["serial.hpp"],
    target_compatible_with = ["@platforms//cpu:armv6-m"],
    deps = [
        "@pico-sdk//src/rp2_common/pico_stdlib",
    ],
)

cc_library(
    name = "transport_zmq",
    srcs = ["host/zmq.cc"],
    hdrs = ["zmq.hpp"],
    deps = [
        "@cppzmq",
        "@libzmq",  # Need to pair this with cppzmq for linkage
    ],
)

cc_library(
    name = "transport_unittest",
    srcs = ["unittest/bent_pipe.cc"],
    hdrs = ["bent_pipe.hpp"],
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
        "@libzmq",  # Need to pair this with cppzmq for linkage
    ],
)
