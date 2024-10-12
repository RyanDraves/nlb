# Heavily inspired by pico-sdk's toolchain configuration,
# although it didn't particularly work.
load("@rules_cc//cc/toolchains:action_type_config.bzl", "cc_action_type_config")
load("@rules_cc//cc/toolchains:tool.bzl", "cc_tool")

package(default_visibility = ["//visibility:public"])

cc_tool(
    name = "xtensa-esp32s3-elf-ar_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/xtensa-esp32s3-elf-ar.exe",
        "//conditions:default": "//:bin/xtensa-esp32s3-elf-ar",
    }),
    data = select({
        # "@platforms//os:windows": [],
        "//conditions:default": ["//:bin/clang-16"],
    }),
)

cc_action_type_config(
    name = "xtensa-esp32s3-elf-ar",
    action_types = ["@rules_cc//cc/toolchains/actions:ar_actions"],
    tools = [":xtensa-esp32s3-elf-ar_tool"],
)

cc_tool(
    name = "clang_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/clang.exe",
        "//conditions:default": "//:bin/clang-16",
    }),
    data = glob([
        "include/armv*-unknown-none-eabi/**",
        "lib/clang/*/include/**",
    ]) + select({
        # "@platforms//os:windows": [],
        "//conditions:default": ["//:bin/clang-16"],
    }),
)

cc_action_type_config(
    name = "clang",
    action_types = [
        "@rules_cc//cc/toolchains/actions:assembly_actions",
        "@rules_cc//cc/toolchains/actions:c_compile",
    ],
    tools = [":clang_tool"],
)

cc_tool(
    name = "clang++_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/clang++.exe",
        "//conditions:default": "//:bin/clang-16",
    }),
    data = glob([
        "include/armv*-unknown-none-eabi/**",
        "include/c++/**",
        "lib/clang/*/include/**",
    ]) + select({
        # Windows doesn't have llvm.exe.
        # "@platforms//os:windows": [],
        "//conditions:default": ["//:bin/clang-16"],
    }),
)

cc_action_type_config(
    name = "clang++",
    action_types = ["@rules_cc//cc/toolchains/actions:cpp_compile_actions"],
    tools = [":clang++_tool"],
)

# This tool is actually just clang++ under the hood, but this specifies a
# different set of data files to pull into the sandbox at runtime.
cc_tool(
    name = "lld_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/clang++.exe",
        "//conditions:default": "//:bin/clang-16",
    }),
    data = glob([
        "lib/armv*-unknown-none-eabi/**",
        "lib/clang/*/lib/armv*-unknown-none-eabi/**",
    ]) + select({
        # "@platforms//os:windows": [],
        "//conditions:default": ["//:bin/clang-16"],
    }),
)

cc_action_type_config(
    name = "lld",
    action_types = ["@rules_cc//cc/toolchains/actions:link_actions"],
    tools = [":lld_tool"],
)

cc_tool(
    name = "xtensa-esp32s3-elf-objcopy_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/xtensa-esp32s3-elf-objcopy.exe",
        "//conditions:default": "//:bin/xtensa-esp32s3-elf-objcopy",
    }),
    data = select({
        # "@platforms//os:windows": [],
        "//conditions:default": ["//:bin/clang-16"],
    }),
)

cc_action_type_config(
    name = "xtensa-esp32s3-elf-objcopy",
    action_types = ["@rules_cc//cc/toolchains/actions:objcopy_embed_data"],
    tools = [":xtensa-esp32s3-elf-objcopy_tool"],
)

cc_tool(
    name = "xtensa-esp32s3-elf-strip_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/xtensa-esp32s3-elf-strip.exe",
        "//conditions:default": "//:bin/xtensa-esp32s3-elf-strip",
    }),
    data = select({
        # "@platforms//os:windows": [],
        "//conditions:default": ["//:bin/clang-16"],
    }),
)

cc_action_type_config(
    name = "xtensa-esp32s3-elf-strip",
    action_types = ["@rules_cc//cc/toolchains/actions:strip"],
    tools = [":xtensa-esp32s3-elf-strip_tool"],
)

cc_tool(
    name = "xtensa-esp32s3-elf-objdump_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/xtensa-esp32s3-elf-objdump.exe",
        "//conditions:default": "//:bin/xtensa-esp32s3-elf-objdump",
    }),
    data = select({
        # "@platforms//os:windows": [],
        "//conditions:default": ["//:bin/clang-16"],
    }),
)

# There is not yet a well-known action type for llvm-objdump.

cc_tool(
    name = "llvm-profdata_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/llvm-profdata.exe",
        "//conditions:default": "//:bin/llvm-profdata",
    }),
    data = select({
        # "@platforms//os:windows": [],
        "//conditions:default": ["//:bin/clang-16"],
    }),
)

# There is not yet a well-known action type for llvm-profdata.

cc_tool(
    name = "llvm-cov_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/llvm-cov.exe",
        "//conditions:default": "//:bin/llvm-cov",
    }),
    data = select({
        # "@platforms//os:windows": [],
        "//conditions:default": ["//:bin/clang-16"],
    }),
)

# There is not yet a well-known action type for llvm-cov.
