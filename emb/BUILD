load("@pip//:requirements.bzl", "requirement")
load("@rules_pico//pico:defs.bzl", "pico_add_uf2_output", "pico_binary", "pico_build_with_config")
load("@rules_python//python:py_binary.bzl", "py_binary")
load("//bzl/rules:platform_transition.bzl", "platform_transition")

cc_library(
    name = "compile_test",
    srcs = ["compile_test.cpp"],
)

# Build the pico SDK with gcc; it seems to have incompatibilities with g++
platform_transition(
    name = "pico_stdlib_c",
    dep = "@rules_pico//pico:pico_stdlib",
    platform = "//bzl/platforms:pico_c",
)

pico_binary(
    name = "hello.elf",
    srcs = [
        "hello.cpp",
    ],
    deps = [":pico_stdlib_c"],
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
    ],
)
