load("@aspect_rules_ts//ts:defs.bzl", "ts_project")

SRCS = [
    "page.tsx",
    "layout.tsx",
    "mdx.d.ts",
    "clif/page.tsx",
    "satellites/page.tsx",
    "satellites/globe.tsx",
    "satellites/data/missions.ts",
    "satellites/data/tles.json",
] + glob(
    [
        "posts/*/*.tsx",
        "_components/*.tsx",
    ],
)

ts_project(
    name = "app",
    srcs = SRCS,
    assets = glob(["_posts/*.mdx"]),
    declaration = True,
    preserve_jsx = True,
    resolve_json_module = True,
    transpiler = "tsc",
    tsconfig = "//blog:tsconfig",
    visibility = ["//blog:__subpackages__"],
    deps = [
        "//blog:node_modules/@types/react",
        "//blog:node_modules/@types/three",
        "//blog:node_modules/classnames",
        "//blog:node_modules/date-fns",
        "//blog:node_modules/next",
        "//blog:node_modules/satellite.js",
        "//blog:node_modules/shiki",
        "//blog:node_modules/three",
        "//blog/lib",
        "//blog/rust",
    ],
)
