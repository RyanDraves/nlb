load("@aspect_rules_ts//ts:defs.bzl", "ts_project")

SRCS = [
    "api.ts",
    "constants.ts",
]

ts_project(
    name = "lib",
    srcs = SRCS,
    declaration = True,
    preserve_jsx = True,
    resolve_json_module = True,
    transpiler = "tsc",
    tsconfig = "//blog:tsconfig",
    visibility = ["//blog:__subpackages__"],
    deps = [
        "//blog:node_modules/@types/node",
        "//blog/interfaces",
    ],
)
