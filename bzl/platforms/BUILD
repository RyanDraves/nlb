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
    flags = [
        "--@pico-sdk//bazel/config:PICO_STDIO_UART=False",
        "--@pico-sdk//bazel/config:PICO_STDIO_USB=True",
        "--@pico-sdk//bazel/config:PICO_STDIO_SEMIHOSTING=False",
        "--@pico-sdk//bazel/config:PICO_DEFAULT_LINKER_SCRIPT=//emb/project/bootloader:memmap_application",
    ],
    parents = ["@pico-sdk//bazel/platform:rp2040"],
)

platform(
    name = "rp2040_bootloader",
    flags = [
        "--@pico-sdk//bazel/config:PICO_STDIO_UART=False",
        "--@pico-sdk//bazel/config:PICO_STDIO_USB=True",
        "--@pico-sdk//bazel/config:PICO_STDIO_SEMIHOSTING=False",
        "--@pico-sdk//bazel/config:PICO_DEFAULT_LINKER_SCRIPT=//emb/project/bootloader:memmap_bootloader",
    ],
    parents = ["@pico-sdk//bazel/platform:rp2040"],
)

platform(
    name = "rp2040_no_bootloader",
    flags = [
        "--@pico-sdk//bazel/config:PICO_STDIO_UART=False",
        "--@pico-sdk//bazel/config:PICO_STDIO_USB=True",
        "--@pico-sdk//bazel/config:PICO_STDIO_SEMIHOSTING=False",
        "--@pico-sdk//bazel/config:PICO_DEFAULT_LINKER_SCRIPT=@pico-sdk//src/rp2_common/pico_crt0:default_linker_script",
    ],
    parents = ["@pico-sdk//bazel/platform:rp2040"],
)
