load("@pip//:requirements.bzl", "requirement")
load("@rules_cc//cc:defs.bzl", "cc_library")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_py_write", "buffham_template")
load("//bzl/macros:patch.bzl", "patch")
load("//bzl/macros:pico.bzl", "pico_project")
load("//bzl/macros:python.bzl", "py_binary")
load("//bzl/rules:platform_transition.bzl", "platform_transition")

buffham(
    name = "bootloader_bh",
    src = "bootloader.bh",
    cc = True,
    py = True,
    visibility = ["//visibility:public"],
)

buffham_py_write(
    name = "bootloader_bh_py_write",
)

pico_project(
    srcs = ["main.cc"],
    linker_script = ":bootloader_linker_script",
    names = ["bootloader_pico"],
    deps = [
        ":bootloader_bh_cc",
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
    out_file = "memmap_application_patch.ld",
    patch = "memmap_application.patch",
)

buffham_template(
    name = "memmap_application_bh",
    bh = ":bootloader_bh",
    out_file = "memmap_application_bh.ld",
    template = "memmap_application_patch.ld",
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

platform_transition(
    name = "application_linker_script",
    dep = ":memmap_application",
    target_platform = "//bzl/platforms:rp2040",
    visibility = ["//visibility:public"],
)

patch(
    name = "memmap_bootloader_patch",
    src = "@pico-sdk//src/rp2_common/pico_crt0/rp2040:memmap_default.ld",
    out_file = "memmap_bootloader_patch.ld",
    patch = "memmap_bootloader.patch",
)

buffham_template(
    name = "memmap_bootloader_bh",
    bh = ":bootloader_bh",
    out_file = "memmap_bootloader_bh.ld",
    template = "memmap_bootloader_patch.ld",
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

platform_transition(
    name = "bootloader_linker_script",
    dep = ":memmap_bootloader",
    target_platform = "//bzl/platforms:rp2040",
    visibility = ["//visibility:public"],
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

provisions = [
    ("pico", "//emb/project/base:base.bin"),
    ("pico_w", "//emb/project/base:base_w.bin"),
]

# gazelle:python_ignore_files provision.py
[
    py_binary(
        name = "provision_" + name,
        srcs = ["provision.py"],
        # Does not play nice with platforms
        add_completions = False,
        args = [
            "$(location bootloader.bin)",
            "$(location {0})".format(bin),
            "$(location @picotool)",
        ],
        data = [
            "bootloader.bin",
            bin,
            "@picotool",
        ],
        main = "provision.py",
        visibility = ["//visibility:private"],
        deps = [
            requirement("rich-click"),
            ":bootloader_bh_py",
            "//emb/network/transport:usb",
            "//emb/project/base:base_bh_py",
            "//emb/project/base:client",
            "//nlb/util:console_utils",
        ],
    )
    for name, bin in provisions
]

py_binary(
    name = "shell",
    srcs = ["shell.py"],
    add_completions = False,
    visibility = ["//:__subpackages__"],
    deps = [
        "//emb/network/transport:usb",
        "//emb/project/base:base_bh_py",
    ],
)
