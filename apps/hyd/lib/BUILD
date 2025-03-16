load("@aspect_rules_ts//ts:defs.bzl", "ts_project")

SRCS = [
    "db.ts",
]

ts_project(
    name = "lib",
    srcs = SRCS,
    declaration = True,
    preserve_jsx = True,
    resolve_json_module = True,
    transpiler = "tsc",
    tsconfig = "//apps/hyd:tsconfig",
    visibility = ["//apps/hyd:__subpackages__"],
    deps = [
        "//apps/hyd:node_modules/@types/node",
        "//apps/hyd:node_modules/@types/pg",
        "//apps/hyd:node_modules/pg",
    ],
)
