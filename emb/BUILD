load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("@pip//:requirements.bzl", "requirement")
load("@rules_pico//pico:defs.bzl", "pico_add_uf2_output", "pico_binary", "pico_build_with_config")

pico_binary(
    name = "hello.elf",
    srcs = [
        "hello.cpp",
    ],
    deps = [
        "//bzl/deps:pico_stdlib_c",
        "//emb/util:cobs",
        "@nlohmann_json//:json",
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
        requirement("cbor2"),
        "//emb/bindings:util",
    ],
)
