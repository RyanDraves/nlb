package(default_visibility = ["//visibility:public"])

constraint_setting(
    name = "host_type",
)

constraint_value(
    name = "unittest",
    constraint_setting = ":host_type",
)

platform(
    name = "host_unittest",
    constraint_values = [
        ":unittest",
    ],
    parents = ["@platforms//host"],
)

# Link to config options:
# https://github.com/raspberrypi/pico-sdk/blob/master/bazel/config/BUILD.bazel
platform(
    name = "rp2040",
    # Additionally, `@pico-sdk//bazel/config:PICO_DEFAULT_LINKER_SCRIPT` is flexibly
    # set in `//bzl/rules:pico.bzl`
    flags = [
        "--@pico-sdk//bazel/config:PICO_STDIO_UART=False",
        "--@pico-sdk//bazel/config:PICO_STDIO_USB=True",
        "--@pico-sdk//bazel/config:PICO_STDIO_SEMIHOSTING=False",
        "--//emb/project/base:pio_blink=True",
    ],
    parents = ["@pico-sdk//bazel/platform:rp2040"],
)

platform(
    name = "rp2040_w",
    flags = [
        "--@pico-sdk//bazel/config:PICO_STDIO_UART=False",
        "--@pico-sdk//bazel/config:PICO_STDIO_USB=True",
        "--@pico-sdk//bazel/config:PICO_STDIO_SEMIHOSTING=False",
        "--@pico-sdk//bazel/config:PICO_BT_ENABLE_BLE=True",
        "--@pico-sdk//bazel/config:PICO_BOARD=pico_w",
        "--@pico-sdk//bazel/config:PICO_BTSTACK_CONFIG=//emb/network/transport:btstack_config",
        # See https://github.com/raspberrypi/pico-sdk/issues/2139
        "--@pico-sdk//bazel/config:PICO_MULTICORE_ENABLED=False",
    ],
    parents = ["@pico-sdk//bazel/platform:rp2040"],
)
