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

# TODO: File ticket for pico_add_bin_output & pico_add_map_output back at
# bazel-arm-none-eabi; the toolchain executable paths are wrong and I
# couldn't figure it out after a couple hours.
genrule(
    name = "hello.bin",
    srcs = [":hello_usb.elf"],
    outs = ["hello.bin"],
    cmd = "$(execpath @arm_none_eabi//:objcopy) -O binary $< $@",
    tools = ["@arm_none_eabi//:objcopy"],
)

genrule(
    name = "hello.map",
    srcs = [":hello_usb.elf"],
    outs = ["hello.map"],
    cmd = "$(execpath @arm_none_eabi//:objdump) -C --all-headers $< > $@",
    tools = ["@arm_none_eabi//:objdump"],
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
