load("@aspect_rules_ts//ts:defs.bzl", "ts_project")

SRCS = [
    "author.ts",
    "post.ts",
]

ts_project(
    name = "interfaces",
    srcs = SRCS,
    declaration = True,
    preserve_jsx = True,
    resolve_json_module = True,
    transpiler = "tsc",
    tsconfig = "//blog:tsconfig",
    visibility = ["//blog:__subpackages__"],
    deps = [
    ],
)
