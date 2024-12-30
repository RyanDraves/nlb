load("@aspect_rules_ts//ts:defs.bzl", "ts_project")

SRCS = glob(
    [
        "*.tsx",
    ],
)

ts_project(
    name = "rust",
    srcs = SRCS,
    declaration = True,
    preserve_jsx = True,
    resolve_json_module = True,
    transpiler = "tsc",
    tsconfig = "//blog:tsconfig",
    visibility = ["//blog:__subpackages__"],
    deps = [
        "//blog:node_modules/@nlb/lrb",
        "//blog:node_modules/@types/react",
        "//blog:node_modules/next",
    ],
)
