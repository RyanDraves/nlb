load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@bazel_skylib//rules:write_file.bzl", "write_file")
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

# This library will automatically resolve to the transport layer picked by the
# `//bzl/configs:COMMS_PROTOCOL` flag
cc_library(
    name = "comms_transport",
    hdrs = [":comms_transport_hpp"],
    visibility = ["//visibility:public"],
    deps = [
        ":comms_transport_lib",
    ],
)

# This library will automatically resolve to the transport layer picked by the
# `//bzl/configs:LOG_PROTOCOL` flag
cc_library(
    name = "log_transport",
    hdrs = [":log_transport_hpp"],
    visibility = ["//visibility:public"],
    deps = [
        ":log_transport_lib",
    ],
)

# Magically pick the correct library
alias(
    name = "comms_transport_lib",
    actual = select(
        {
            "//bzl/constraints:comms_protocol_ble_enabled": ":transport_ble",
            "//bzl/constraints:comms_protocol_serial_enabled": ":transport_serial",
            "//bzl/constraints:comms_protocol_zmq_enabled": ":transport_zmq",
            "//bzl/constraints:comms_protocol_unittest_enabled": ":transport_unittest",
        },
    ),
)

alias(
    name = "log_transport_lib",
    actual = select(
        {
            "//bzl/constraints:log_protocol_ble_enabled": ":transport_ble",
            "//bzl/constraints:log_protocol_serial_enabled": ":transport_serial",
            "//bzl/constraints:log_protocol_zmq_enabled": ":transport_zmq",
            "//bzl/constraints:log_protocol_unittest_enabled": ":transport_unittest",
        },
    ),
)

# There's probably a better way to handle this, but it suffices for now.
# This rule generates a header file that includes the correct transport layer
# and aliases it to `CommsTransport`.
write_file(
    name = "comms_transport_hpp",
    out = "comms_transport.hpp",
    content =
        select(
            {
                "//bzl/constraints:comms_protocol_ble_enabled": ["#include \"emb/network/transport/ble.hpp\""],
                "//bzl/constraints:comms_protocol_serial_enabled": ["#include \"emb/network/transport/serial.hpp\""],
                "//bzl/constraints:comms_protocol_zmq_enabled": ["#include \"emb/network/transport/zmq.hpp\""],
                "//bzl/constraints:comms_protocol_unittest_enabled": ["#include \"emb/network/transport/bent_pipe.hpp\""],
            },
        ) + [
            "namespace emb { namespace network { namespace transport {",
        ] + select(
            {
                "//bzl/constraints:comms_protocol_ble_enabled": ["using CommsTransport = Ble;"],
                "//bzl/constraints:comms_protocol_serial_enabled": ["using CommsTransport = Serial;"],
                "//bzl/constraints:comms_protocol_zmq_enabled": ["using CommsTransport = Zmq;"],
                "//bzl/constraints:comms_protocol_unittest_enabled": ["using CommsTransport = BentPipe;"],
            },
        ) + [
            "} } }",
        ],
)

write_file(
    name = "log_transport_hpp",
    out = "log_transport.hpp",
    content =
        select(
            {
                "//bzl/constraints:log_protocol_ble_enabled": ["#include \"emb/network/transport/ble.hpp\""],
                "//bzl/constraints:log_protocol_serial_enabled": ["#include \"emb/network/transport/serial.hpp\""],
                "//bzl/constraints:log_protocol_zmq_enabled": ["#include \"emb/network/transport/zmq.hpp\""],
                "//bzl/constraints:log_protocol_unittest_enabled": ["#include \"emb/network/transport/bent_pipe.hpp\""],
            },
        ) + [
            "namespace emb { namespace network { namespace transport {",
        ] + select(
            {
                "//bzl/constraints:log_protocol_ble_enabled": ["using LogTransport = Ble;"],
                "//bzl/constraints:log_protocol_serial_enabled": ["using LogTransport = Serial;"],
                "//bzl/constraints:log_protocol_zmq_enabled": ["using LogTransport = Zmq;"],
                "//bzl/constraints:log_protocol_unittest_enabled": ["using LogTransport = BentPipe;"],
            },
        ) + [
            "} } }",
        ],
)

# Back to sanity; these are the real libraries implementing the transport layers
cc_library(
    name = "transport_ble",
    srcs = ["pico/ble.cc"],
    hdrs = ["ble.hpp"],
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
    deps = ["@cppzmq"],
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
    ],
)
