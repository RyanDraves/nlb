package(default_visibility = ["//visibility:public"])

platform(
    name = "host_unittest",
    constraint_values = [
        "//bzl/constraints:unittest",
    ],
    flags = [
        "--//bzl/configs:COMMS_PROTOCOL=unittest",
    ],
    parents = ["@platforms//host"],
)

platform(
    name = "linux_amd64",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
)

platform(
    name = "linux_arm64",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:arm64",
    ],
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
        "--//bzl/configs:PIO_BLINK=True",
        "--//bzl/configs:COMMS_PROTOCOL=serial",
        "--//bzl/configs:LOG_PROTOCOL=serial",
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
        "--//bzl/configs:COMMS_PROTOCOL=ble",
        "--//bzl/configs:LOG_PROTOCOL=serial",
    ],
    parents = ["@pico-sdk//bazel/platform:rp2040"],
)

platform(
    name = "rbe_platform",
    constraint_values = [
        "@platforms//cpu:x86_64",
        "@platforms//os:linux",
        "@bazel_tools//tools/cpp:gcc",
    ],
    exec_properties = {
        "OSFamily": "Linux",
        "dockerNetwork": "off",
        "container-image": "docker://ghcr.io/ryandraves/env:lld",
    },
)
