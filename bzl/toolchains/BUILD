load("@arm_none_eabi//toolchain:toolchain.bzl", "arm_none_eabi_toolchain")

package(default_visibility = ["//visibility:public"])

arm_none_eabi_toolchain(
    name = "g++-pico",
    copts = [
        "-mcpu=cortex-m0plus",
        "-mthumb",
        "-std=c++23",
    ],
    gcc_tool = "g++",
    target_compatible_with = [
        "@platforms//os:none",
        "@platforms//cpu:armv6-m",
        "//bzl/platforms:23",
    ],
    version = "13.2.1",
)

arm_none_eabi_toolchain(
    name = "gcc-pico",
    copts = [
        "-mcpu=cortex-m0plus",
        "-mthumb",
    ],
    gcc_tool = "gcc",
    target_compatible_with = [
        "@platforms//os:none",
        "@platforms//cpu:armv6-m",
        "//bzl/platforms:c",
    ],
    version = "13.2.1",
)
