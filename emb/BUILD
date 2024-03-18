load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("@rules_pico//pico:defs.bzl", "pico_add_uf2_output", "pico_binary", "pico_build_with_config")
load("//bzl/rules:platform_transition.bzl", "platform_transition")

exports_files(["system.fbs"])

# Build the pico SDK with gcc; it seems to have incompatibilities with g++
platform_transition(
    name = "pico_stdlib_c",
    dep = "@rules_pico//pico:pico_stdlib",
    platform = "//bzl/platforms:pico_c",
    visibility = ["//:__subpackages__"],
)

pico_binary(
    name = "hello.elf",
    srcs = [
        "hello.cpp",
    ],
    deps = [
        ":pico_stdlib_c",
        ":system_cc_bebop",
        "//emb/util:cobs",
        "//third_party/bebop",
    ],
)

pico_build_with_config(
    name = "hello_usb.elf",
    input = "hello.elf",
    stdio_uart = False,
    stdio_usb = True,
)

pico_add_uf2_output(
    name = "hello.uf2",
    input = "hello_usb.elf",
)

py_binary(
    name = "client",
    srcs = ["client.py"],
    deps = [
        requirement("pyserial"),
        ":system_py_bebop",
        "//emb/bindings:util",
    ],
)

# TODO: Generate
cc_library(
    name = "system_cc_bebop",
    hdrs = ["system.hpp"],
    deps = ["//third_party/bebop"],
)

py_library(
    name = "system_py_bebop",
    srcs = ["system.py"],
    deps = [
        requirement("python_bebop"),
    ],
)
