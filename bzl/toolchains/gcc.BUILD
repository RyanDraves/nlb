# This file is unused; just WIP efforts to get the xtensa gcc toolchain working
load("@pico-sdk//bazel/toolchain:configurable_feature.bzl", "configurable_toolchain_feature")
load("@rules_cc//cc/toolchains:args.bzl", "cc_args")
load("@rules_cc//cc/toolchains:args_list.bzl", "cc_args_list")
load("@rules_cc//cc/toolchains:feature.bzl", "cc_feature")
load("@rules_cc//cc/toolchains:toolchain.bzl", "cc_toolchain")

package(default_visibility = ["//visibility:public"])

cc_args(
    name = "xtensa",
    actions = [
        "@rules_cc//cc/toolchains/actions:compile_actions",
        "@rules_cc//cc/toolchains/actions:link_actions",
    ],
    args = [
        # TODO: Figure out what flags are needed from esp-idf.
        # "-mcpu=xtensa",
        # "-mthumb",
        "-MMD",
    ],
)

cc_args(
    name = "no-canonical-system-headers",
    actions = ["@rules_cc//cc/toolchains/actions:compile_actions"],
    args = ["-fno-canonical-system-headers"],
)

cc_args(
    name = "no-canonical-prefixes",
    actions = ["@rules_cc//cc/toolchains/actions:compile_actions"],
    args = ["-no-canonical-prefixes"],
)

cc_args_list(
    name = "bazel_no_absolute_paths",
    args = [
        ":no-canonical-system-headers",
        ":no-canonical-prefixes",
    ],
)

cc_args(
    name = "opt_debug_args",
    actions = [
        "@rules_cc//cc/toolchains/actions:compile_actions",
        "@rules_cc//cc/toolchains/actions:link_actions",
    ],
    args = [
        "-Og",  # TODO: Make this configurable.
        "-g3",
    ],
)

configurable_toolchain_feature(
    name = "gc_sections",
    copts = [
        "-ffunction-sections",
        "-fdata-sections",
    ],
    disable_if = "@pico-sdk//bazel/constraint:pico_no_gc_sections_enabled",
    linkopts = ["-Wl,--gc-sections"],
)

configurable_toolchain_feature(
    name = "cxx_no_exceptions",
    cxxopts = [
        "-fno-exceptions",
        "-fno-unwind-tables",
    ],
    disable_if = "@pico-sdk//bazel/constraint:pico_cxx_enable_exceptions_enabled",
)

configurable_toolchain_feature(
    name = "cxx_no_rtti",
    cxxopts = ["-fno-rtti"],
    disable_if = "@pico-sdk//bazel/constraint:pico_cxx_enable_rtti_enabled",
)

configurable_toolchain_feature(
    name = "cxx_no_cxa_atexit",
    cxxopts = ["-fno-use-cxa-atexit"],
    disable_if = "@pico-sdk//bazel/constraint:pico_cxx_enable_cxa_atexit_enabled",
)

configurable_toolchain_feature(
    name = "override_max_page_size",
    disable_if = "@pico-sdk//bazel/constraint:pico_use_default_max_page_size_enabled",
    linkopts = ["-Wl,-z,max-page-size=4096"],
)

# TODO: Make this shim unnecessary.
cc_args_list(
    name = "all_opt_debug_args",
    args = [":opt_debug_args"],
)

cc_feature(
    name = "override_debug",
    args = [":all_opt_debug_args"],
    enabled = True,
    overrides = "@rules_cc//cc/toolchains/features:dbg",
)

# TODO: https://github.com/bazelbuild/rules_cc/issues/224 - This is required for
# now, but hopefully will eventually go away.
cc_feature(
    name = "legacy_features",
    args = [],
    enabled = True,
    feature_name = "force_legacy_features",
    implies = [
        "@rules_cc//cc/toolchains/features/legacy:archiver_flags",
        "@rules_cc//cc/toolchains/features/legacy:build_interface_libraries",
        "@rules_cc//cc/toolchains/features/legacy:dynamic_library_linker_tool",
        "@rules_cc//cc/toolchains/features/legacy:strip_debug_symbols",
        "@rules_cc//cc/toolchains/features/legacy:linkstamps",
        "@rules_cc//cc/toolchains/features/legacy:output_execpath_flags",
        "@rules_cc//cc/toolchains/features/legacy:runtime_library_search_directories",
        "@rules_cc//cc/toolchains/features/legacy:library_search_directories",
        "@rules_cc//cc/toolchains/features/legacy:libraries_to_link",
        "@rules_cc//cc/toolchains/features/legacy:force_pic_flags",
        "@rules_cc//cc/toolchains/features/legacy:user_link_flags",
        "@rules_cc//cc/toolchains/features/legacy:legacy_link_flags",
        "@rules_cc//cc/toolchains/features/legacy:linker_param_file",
        "@rules_cc//cc/toolchains/features/legacy:fission_support",
        "@rules_cc//cc/toolchains/features/legacy:sysroot",
    ],
)

HOSTS = (
    ("linux", "x86_64"),
    # TODO
    # ("win", "x86_64"),
    # ("mac", "x86_64"),
    # ("mac", "aarch64"),
)

_HOST_OS_CONSTRAINTS = {
    "linux": "@platforms//os:linux",
    "win": "@platforms//os:windows",
    "mac": "@platforms//os:macos",
}

_HOST_CPU_CONSTRAINTS = {
    "x86_64": "@platforms//cpu:x86_64",
    "aarch64": "@platforms//cpu:aarch64",
}

[cc_toolchain(
    name = "xtensa_esp_elf_{}-{}_toolchain_xtensa".format(host_os, host_cpu),
    action_type_configs = [
        "@xtensa_esp_elf_{}-{}//:xtensa-esp32s3-elf-ar".format(host_os, host_cpu),
        "@xtensa_esp_elf_{}-{}//:xtensa-esp32s3-elf-gcc".format(host_os, host_cpu),
        "@xtensa_esp_elf_{}-{}//:xtensa-esp32s3-elf-g++".format(host_os, host_cpu),
        "@xtensa_esp_elf_{}-{}//:xtensa-esp32s3-elf-ld".format(host_os, host_cpu),
        "@xtensa_esp_elf_{}-{}//:xtensa-esp32s3-elf-objcopy".format(host_os, host_cpu),
        "@xtensa_esp_elf_{}-{}//:xtensa-esp32s3-elf-strip".format(host_os, host_cpu),
    ],
    args = select({
        # TODO: Uncomment when flags are figured out.
        # "//bzl/platforms:xtensa": [":xtensa"],
        "//conditions:default": [],
    }) + [
        ":bazel_no_absolute_paths",
    ],
    compiler = "xtensa-gcc",
    cxx_builtin_include_directories = [
        # "%sysroot%/xtensa-esp-elf/include/c++/13.2.0/",
        # "%sysroot%/xtensa-esp-elf/include/c++/13.2.0/xtensa-esp-elf/esp32s3/",
        # "%sysroot%/xtensa-esp-elf/include/c++/13.2.0/backward/",
        # "%sysroot%/lib/gcc/xtensa-esp-elf/13.2.0/include",
        # "%sysroot%/lib/gcc/xtensa-esp-elf/13.2.0/include-fixed/",
        # "%sysroot%/xtensa-esp-elf/include/",
        "/usr/include",
    ],
    exec_compatible_with = [
        _HOST_CPU_CONSTRAINTS[host_cpu],
        _HOST_OS_CONSTRAINTS[host_os],
    ],
    sysroot = "external/xtensa_esp_elf_linux-x86_64",
    tags = ["manual"],  # Don't try to build this in wildcard builds.
    toolchain_features = [
        "@pico-sdk//bazel/toolchain:legacy_features",
        "@pico-sdk//bazel/toolchain:override_debug",
        "@pico-sdk//bazel/toolchain:gc_sections",
        "@pico-sdk//bazel/toolchain:cxx_no_exceptions",
        "@pico-sdk//bazel/toolchain:cxx_no_rtti",
        "@pico-sdk//bazel/toolchain:cxx_no_cxa_atexit",
        "@pico-sdk//bazel/toolchain:override_max_page_size",
    ],
) for host_os, host_cpu in HOSTS]

[toolchain(
    name = "{}-{}-esp32s3".format(host_os, host_cpu),
    exec_compatible_with = [
        _HOST_CPU_CONSTRAINTS[host_cpu],
        _HOST_OS_CONSTRAINTS[host_os],
    ],
    target_compatible_with = [
        "//bzl/platforms:xtensa",
    ],
    toolchain = select({
        "//conditions:default": ":xtensa_esp_elf_{}-{}_toolchain_xtensa".format(host_os, host_cpu),
    }),
    toolchain_type = "@bazel_tools//tools/cpp:toolchain_type",
) for host_os, host_cpu in HOSTS]
