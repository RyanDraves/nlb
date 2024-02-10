load("@com_github_nanopb_nanopb//extra/bazel:nanopb_cc_proto_library.bzl", "cc_nanopb_proto_library")
load("@pip//:requirements.bzl", "requirement")
load("@rules_pico//pico:defs.bzl", "pico_add_uf2_output", "pico_binary", "pico_build_with_config")
load("@rules_proto//proto:defs.bzl", "proto_library")
load("@rules_python//python:py_binary.bzl", "py_binary")
load("//bzl/rules:platform_transition.bzl", "platform_transition")

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
    deps = [
        ":hello_nanopb_proto",
        ":pico_stdlib_c",
        "@com_github_nanopb_nanopb//:nanopb",
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
    ],
)

proto_library(
    name = "hello_proto",
    srcs = ["hello.proto"],
)

# platform_transition(
#     name = "hello_proto_host",
#     dep = ":hello_proto",
#     platform = "@local_config_platform//:host",
# )

cc_nanopb_proto_library(
    name = "hello_nanopb_proto",
    protos = [":hello_proto"],
)
