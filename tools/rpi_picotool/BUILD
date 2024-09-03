load("@rules_foreign_cc//foreign_cc:defs.bzl", "cmake")

cmake(
    name = "picotool",
    data = [
        "@picotool//:pico_sdk_files",
        # Depend on an individual file so we can get an `execpath` to the repo root
        "@picotool//:pico_sdk_repo/README.md",
    ],
    env = {
        "PICO_SDK_PATH": "$$(dirname $(execpath @picotool//:pico_sdk_repo/README.md))",
    },
    lib_source = "@picotool//:picotool_files",
    out_binaries = ["picotool"],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "picotool_bin",
    srcs = [":picotool"],
    # See https://stackoverflow.com/a/61282031 to list output_groups of a target;
    # this gets us just the final binary
    output_group = "picotool",
    visibility = ["//visibility:public"],
)
