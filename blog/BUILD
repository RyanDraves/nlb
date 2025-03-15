load("@aspect_rules_js//js:defs.bzl", "js_library")
load("@aspect_rules_ts//ts:defs.bzl", "ts_config", "ts_project")
load("@bazel_skylib//rules:build_test.bzl", "build_test")
load("@npm//:defs.bzl", "npm_link_all_packages")
load("@npm//blog:next/package_json.bzl", next_bin = "bin")
load("@npm//blog:tailwindcss/package_json.bzl", tailwind_bin = "bin")
load("//bzl/macros:next.bzl", "next")

npm_link_all_packages(name = "node_modules")

_SRCS = [
    "//blog/app",
    "//blog/interfaces",
    "//blog/rust",
    "//blog/lib",
    "//blog/public",
    "//blog/styles",
    ":mdx_components",
]

next_bin.next_binary(
    name = "next_js_binary",
    visibility = ["//visibility:public"],
)

ts_config(
    name = "tsconfig",
    src = "tsconfig.json",
    visibility = ["//visibility:public"],
)

ts_project(
    name = "mdx_components",
    srcs = ["mdx-components.tsx"],
    declaration = True,
    preserve_jsx = True,
    resolve_json_module = True,
    transpiler = "tsc",
    tsconfig = ":tsconfig",
    visibility = [":__subpackages__"],
    deps = [
        ":node_modules/@types/mdx",
    ],
)

next(
    name = "next",
    srcs = _SRCS + [
        ":tailwind",
    ],
    data = [
        "next.config.ts",
        "tsconfig.json",
        ":node_modules/@next/mdx",
        ":node_modules/autoprefixer",
        ":node_modules/next",
        ":node_modules/postcss",
        ":node_modules/react",
        ":node_modules/react-dom",
        ":node_modules/typescript",
    ],
    is_exported = True,
    next_bin = "./node_modules/next/dist/bin/next",
    next_js_binary = ":next_js_binary",
)

tailwind_bin.tailwind(
    name = "tailwind",
    srcs = _SRCS + [
        ":node_modules/@tailwindcss/typography",
        ":tailwind_config",
    ],
    outs = ["tailwind.css"],
    args = [
        "--output",
        "tailwind.css",
    ],
    chdir = package_name(),
)

js_library(
    name = "tailwind_config",
    srcs = [
        "tailwind.config.ts",
    ],
    deps = [
    ],
)

build_test(
    name = "build_test",
    targets = [
        ":next",
    ],
)
