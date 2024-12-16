load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pico-sdk//bazel:pico_btstack_make_gatt_header.bzl", "pico_btstack_make_gatt_header")
load("@pip//:requirements.bzl", "requirement")
load("@rules_cc//cc:defs.bzl", "cc_library")
load("//bzl/macros:unittest.bzl", "cc_host_test", "cc_unittest")

pico_btstack_make_gatt_header(
    name = "nus",
    src = "nus.gatt",
)

py_library(
    name = "ble",
    srcs = ["ble.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("bleak"),
    ],
)

cc_library(
    name = "ble_cc",
    srcs = select(
        {
            "@platforms//cpu:armv6-m": ["pico/ble.cc"],
            "//conditions:default": [],
        },
    ),
    hdrs = ["ble.hpp"],
    visibility = ["//visibility:public"],
    deps = select(
        {
            "@platforms//cpu:armv6-m": [
                ":nus",
                "@pico-sdk//src/common/pico_sync",
                "@pico-sdk//src/rp2_common/pico_btstack",
                "@pico-sdk//src/rp2_common/pico_cyw43_arch",
            ],
            "//conditions:default": [],
        },
    ),
)

cc_library(
    name = "btstack_config",
    hdrs = ["btstack_config.h"],
    includes = ["."],  # Shorten the include path to what dependents expect
    visibility = ["//visibility:public"],
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

cc_library(
    name = "transporter_cc",
    hdrs = ["transporter.hpp"],
    visibility = ["//visibility:public"],
)

cc_library(
    name = "serial_cc",
    srcs = select(
        {
            "@platforms//cpu:armv6-m": ["pico/serial.cc"],
            "//bzl/platforms:unittest": ["unittest/serial.cc"],
            "//conditions:default": ["host/serial.cc"],
        },
    ),
    hdrs = ["serial.hpp"],
    visibility = ["//visibility:public"],
    deps = select(
        {
            "@platforms//cpu:armv6-m": [
                "@pico-sdk//src/rp2_common/pico_cyw43_arch",
                "@pico-sdk//src/rp2_common/pico_stdlib",
            ],
            "//bzl/platforms:unittest": [":transporter_cc"],
            "//conditions:default": ["@cppzmq"],
        },
    ),
)

cc_unittest(
    name = "serial_cc_test",
    srcs = ["unittest/serial_test.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":serial_cc",
    ],
)

cc_host_test(
    name = "serial_host_test",
    srcs = ["host/serial_test.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":serial_cc",
        "@cppzmq",
    ],
)
