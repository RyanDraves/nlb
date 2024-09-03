filegroup(
    name = "picotool_files",
    srcs = glob(["picotool_repo/**/*"]),
    visibility = ["//visibility:public"],
)

filegroup(
    name = "pico_sdk_files",
    srcs = glob(["pico_sdk_repo/**/*"]),
    visibility = ["//visibility:public"],
)

# Expose an individual file from each repo so `$(location)` macros
# can be used to get the repo roots
exports_files(
    [
        "picotool_repo/README.md",
        "pico_sdk_repo/README.md",
    ],
)
