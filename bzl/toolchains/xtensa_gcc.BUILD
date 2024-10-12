# This file is unused; just WIP efforts to get the xtensa gcc toolchain working
load("@rules_cc//cc/toolchains:action_type_config.bzl", "cc_action_type_config")
load("@rules_cc//cc/toolchains:tool.bzl", "cc_tool")

package(default_visibility = ["//visibility:public"])

cc_tool(
    name = "xtensa-esp32s3-elf-ar_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/xtensa-esp32s3-elf-ar.exe",
        "//conditions:default": "//:bin/xtensa-esp32s3-elf-ar",
    }),
)

cc_action_type_config(
    name = "xtensa-esp32s3-elf-ar",
    action_types = ["@rules_cc//cc/toolchains/actions:ar_actions"],
    tools = [":xtensa-esp32s3-elf-ar_tool"],
)

cc_tool(
    name = "xtensa-esp32s3-elf-g++_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/xtensa-esp32s3-elf-g++.exe",
        "//conditions:default": "//:bin/xtensa-esp32s3-elf-g++",
    }),
    data = glob([
        "**/*.spec",
        "**/*.specs",
        "xtensa-esp-elf/include/**",
        "lib/gcc/xtensa-esp-elf/*/include/**",
        "lib/gcc/xtensa-esp-elf/*/include-fixed/**",
        "libexec/**",
    ]),
)

cc_action_type_config(
    name = "xtensa-esp32s3-elf-g++",
    action_types = ["@rules_cc//cc/toolchains/actions:cpp_compile_actions"],
    tools = [":xtensa-esp32s3-elf-g++_tool"],
)

cc_tool(
    name = "xtensa-esp32s3-elf-gcc_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/xtensa-esp32s3-elf-gcc.exe",
        "//conditions:default": "//:bin/xtensa-esp32s3-elf-gcc",
    }),
    data = glob([
        "**/*.spec",
        "**/*.specs",
        "xtensa-esp-elf/include/**",
        "lib/gcc/xtensa-esp-elf/*/include/**",
        "lib/gcc/xtensa-esp-elf/*/include-fixed/**",
        "libexec/**",
    ]) +
    # The assembler needs to be explicitly added. Note that the path is
    # intentionally different here as `as` is called from xtensa-esp32s3-elf-gcc.
    # `xtensa-esp32s3-elf-as` will not suffice for this context.
    select({
        # "@platforms//os:windows": ["//:xtensa-esp-elf/bin/as.exe"],
        "//conditions:default": ["//:xtensa-esp-elf/bin/as"],
    }),
)

cc_action_type_config(
    name = "xtensa-esp32s3-elf-gcc",
    action_types = [
        "@rules_cc//cc/toolchains/actions:assembly_actions",
        "@rules_cc//cc/toolchains/actions:c_compile",
    ],
    tools = [":xtensa-esp32s3-elf-gcc_tool"],
)

# This tool is actually just g++ under the hood, but this specifies a
# different set of data files to pull into the sandbox at runtime.
cc_tool(
    name = "xtensa-esp32s3-elf-ld_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/xtensa-esp32s3-elf-g++.exe",
        "//conditions:default": "//:bin/xtensa-esp32s3-elf-g++",
    }),
    data = glob([
        "**/*.a",
        "**/*.ld",
        "**/*.o",
        "**/*.spec",
        "**/*.specs",
        "**/*.so",
        "libexec/**",
    ]),
)

cc_action_type_config(
    name = "xtensa-esp32s3-elf-ld",
    action_types = ["@rules_cc//cc/toolchains/actions:link_actions"],
    tools = [":xtensa-esp32s3-elf-ld_tool"],
)

cc_tool(
    name = "xtensa-esp32s3-elf-objcopy_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/xtensa-esp32s3-elf-objcopy.exe",
        "//conditions:default": "//:bin/xtensa-esp32s3-elf-objcopy",
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
)

# There is not yet a well-known action type for objdump.

cc_tool(
    name = "xtensa-esp32s3-elf-gcov_tool",
    src = select({
        # "@platforms//os:windows": "//:bin/xtensa-esp32s3-elf-gcov.exe",
        "//conditions:default": "//:bin/xtensa-esp32s3-elf-gcov",
    }),
)

# There is not yet a well-known action type for gcov.
