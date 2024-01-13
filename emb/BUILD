load("@rules_pico//pico:defs.bzl", "pico_binary")
load("@rules_pico//pico:defs.bzl", "pico_build_with_config")
load("@rules_pico//pico:defs.bzl", "pico_add_uf2_output")

pico_binary(
    name = "hello.elf",
    srcs = [
        "hello.c",
    ],
    deps = [
        "@rules_pico//pico:pico_stdlib",
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
