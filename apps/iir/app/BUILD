load("@aspect_rules_ts//ts:defs.bzl", "ts_project")

SRCS = [
    "page.tsx",
    "layout.tsx",
    "api/weather/route.ts",
]

ts_project(
    name = "app",
    srcs = SRCS,
    declaration = True,
    preserve_jsx = True,
    resolve_json_module = True,
    transpiler = "tsc",
    tsconfig = "//apps/iir:tsconfig",
    visibility = ["//apps/iir:__subpackages__"],
    deps = [
        "//apps/iir:node_modules/@types/node",
        "//apps/iir:node_modules/@types/react",
        "//apps/iir:node_modules/next",
    ],
)
