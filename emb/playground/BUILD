load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("@com_github_google_flatbuffers//:build_defs.bzl", "flatbuffer_cc_library")
load("@com_github_nanopb_nanopb//extra/bazel:nanopb_cc_proto_library.bzl", "cc_nanopb_proto_library")
load("@com_google_protobuf//:protobuf.bzl", "py_proto_library")
load("@pip//:requirements.bzl", "requirement")
load("@rules_pico//pico:defs.bzl", "pico_add_uf2_output", "pico_binary", "pico_build_with_config")
load("@rules_proto//proto:defs.bzl", "proto_library")
load("//bzl/macros:flatbuffer_py_library.bzl", "flatbuffer_py_library")
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
    name = "hello_fb.elf",
    srcs = [
        "hello_fb.cpp",
    ],
    deps = [
        ":pico_stdlib_c",
        ":system_cc_fbs_host",
        ":system_nanopb_proto",
        "//emb/util:cobs",
        "@com_github_nanopb_nanopb//:nanopb",
    ],
)

pico_build_with_config(
    name = "hello_fb_usb.elf",
    input = "hello_fb.elf",
    stdio_uart = False,
    stdio_usb = True,
)

pico_add_uf2_output(
    name = "hello_fb.uf2",
    input = "hello_fb_usb.elf",
)

pico_binary(
    name = "hello_pb.elf",
    srcs = [
        "hello_pb.cpp",
    ],
    deps = [
        ":pico_stdlib_c",
        ":system_nanopb_proto",
        "//emb/util:cobs",
        "@com_github_nanopb_nanopb//:nanopb",
    ],
)

pico_build_with_config(
    name = "hello_pb_usb.elf",
    input = "hello_pb.elf",
    stdio_uart = False,
    stdio_usb = True,
)

pico_add_uf2_output(
    name = "hello_pb.uf2",
    input = "hello_pb_usb.elf",
)

py_binary(
    name = "client_bop",
    srcs = ["client_bop.py"],
    deps = [
        requirement("pyserial"),
        ":system_py_bebop",
        "//emb/bindings:util",
    ],
)

py_binary(
    name = "client_fb",
    srcs = ["client_fb.py"],
    deps = [
        requirement("pyserial"),
        requirement("flatbuffers"),
        ":system_py_fbs",
        "//emb/bindings:util",
    ],
)

py_binary(
    name = "client_pb",
    srcs = ["client_pb.py"],
    deps = [
        requirement("pyserial"),
        ":system_py_proto",
        "//emb/bindings:util",
    ],
)

proto_library(
    name = "system_proto",
    srcs = ["system.proto"],
)

cc_nanopb_proto_library(
    name = "system_nanopb_proto",
    protos = [":system_proto"],
)

py_proto_library(
    name = "system_py_proto",
    srcs = ["system.proto"],
)

flatbuffer_cc_library(
    name = "system_cc_fbs",
    srcs = ["system.fbs"],
)

# Generate the flatbuffer headers with the host toolchain;
# the arm toolchain doesn't have stdlib things like std::string
platform_transition(
    name = "system_cc_fbs_host",
    dep = ":system_cc_fbs",
    platform = "@local_config_platform//:host",
)

flatbuffer_py_library(
    name = "system_py_fbs",
    srcs = [
        "system.fbs",
    ],
    outs = ["system_generated.py"],
)
