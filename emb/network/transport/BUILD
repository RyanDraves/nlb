load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:cc.bzl", "cc_host_test", "cc_library", "cc_unittest")

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
