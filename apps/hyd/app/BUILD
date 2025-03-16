load("@aspect_rules_ts//ts:defs.bzl", "ts_project")

SRCS = [
    "page.tsx",
    "layout.tsx",
    "api/progress/[id]/route.ts",
    "api/progress/route.ts",
]

ts_project(
    name = "app",
    srcs = SRCS,
    declaration = True,
    preserve_jsx = True,
    resolve_json_module = True,
    transpiler = "tsc",
    tsconfig = "//apps/hyd:tsconfig",
    visibility = ["//apps/hyd:__subpackages__"],
    deps = [
        "//apps/hyd:node_modules/@fortawesome/free-solid-svg-icons",
        "//apps/hyd:node_modules/@fortawesome/react-fontawesome",
        "//apps/hyd:node_modules/@types/react",
        "//apps/hyd:node_modules/next",
        "//apps/hyd/lib",
    ],
)
