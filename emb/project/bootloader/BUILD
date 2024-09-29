load("//bzl/macros:buffham.bzl", "buffham", "buffham_cc_library", "buffham_py_library", "buffham_template")
load("//bzl/macros:patch.bzl", "patch")
load("//bzl/macros:pico.bzl", "pico_project")
load("//bzl/rules:platform_transition.bzl", "platform_transition")

platform_transition(
    name = "application_linker_script",
    dep = ":memmap_application",
    platform = "@pico-sdk//bazel/platform:rp2040",
    visibility = ["//visibility:public"],
)

platform_transition(
    name = "bootloader_linker_script",
    dep = ":memmap_bootloader",
    platform = "@pico-sdk//bazel/platform:rp2040",
    visibility = ["//visibility:public"],
)

buffham(
    name = "bootloader_bh",
    srcs = ["bootloader.bh"],
)

buffham_py_library(
    name = "bootloader_bh_py",
    bh = ":bootloader_bh",
)

buffham_cc_library(
    name = "bootloader_bh_cc",
    bh = ":bootloader_bh",
)

pico_project(
    name = "bootloader_pico",
    srcs = ["main.cc"],
    linker_script = ":bootloader_linker_script",
    deps = [
        ":bootloader_bh_cc",
        "//emb/network/serialize:bh_cobs_cc",
        "//emb/network/transport:serial_cc",
        "//emb/project/base:base_bh_cc",
        "//emb/yaal:flash",
        "@pico-sdk//src/rp2_common:hardware_structs",
        "@pico-sdk//src/rp2_common/hardware_flash",
        "@pico-sdk//src/rp2_common/hardware_gpio",
        "@pico-sdk//src/rp2_common/pico_stdlib",
    ],
)

patch(
    name = "memmap_application_patch",
    src = "@pico-sdk//src/rp2_common/pico_crt0/rp2040:memmap_default.ld",
    out_file = "memmap_application.ld",
    patch = "memmap_application.patch",
)

buffham_template(
    name = "memmap_application_template",
    bh = ":bootloader_bh",
    out_file = "memmap_application_bh.ld",
    template = "memmap_application.ld",
    visibility = ["//visibility:public"],
)

cc_library(
    name = "memmap_application",
    linkopts = ["-T$(location memmap_application_bh.ld)"],
    target_compatible_with = ["@pico-sdk//bazel/constraint:rp2040"],
    deps = [
        "memmap_application_bh.ld",
        ":no_warn_rwx_flag",
        "@pico-sdk//src/rp2_common/pico_standard_link:default_flash_region",
    ],
)

patch(
    name = "memmap_bootloader_patch",
    src = "@pico-sdk//src/rp2_common/pico_crt0/rp2040:memmap_default.ld",
    out_file = "memmap_bootloader.ld",
    patch = "memmap_bootloader.patch",
)

buffham_template(
    name = "memmap_bootloader_template",
    bh = ":bootloader_bh",
    out_file = "memmap_bootloader_bh.ld",
    template = "memmap_bootloader.ld",
    visibility = ["//visibility:public"],
)

cc_library(
    name = "memmap_bootloader",
    linkopts = [
        "-T$(location memmap_bootloader_bh.ld)",
    ],
    target_compatible_with = ["@pico-sdk//bazel/constraint:rp2040"],
    deps = [
        "memmap_bootloader_bh.ld",
        ":no_warn_rwx_flag",
        "@pico-sdk//src/rp2_common/pico_standard_link:default_flash_region",
    ],
)

# Taken from the Pico SDK; wasn't marked public
cc_library(
    name = "no_warn_rwx_flag",
    linkopts = select({
        "@pico-sdk//bazel/constraint:pico_toolchain_gcc_enabled": ["-Wl,--no-warn-rwx-segments"],
        "//conditions:default": [],
    }),
    visibility = [":__subpackages__"],
)
