load("@aspect_rules_js//js:defs.bzl", "js_library")
load("@aspect_rules_ts//ts:defs.bzl", "ts_config")
load("@bazel_skylib//rules:build_test.bzl", "build_test")
load("@npm//:defs.bzl", "npm_link_all_packages")
load("@npm//blog:next/package_json.bzl", next_bin = "bin")
load("@npm//blog:tailwindcss/package_json.bzl", tailwind_bin = "bin")
load("//bzl/macros:next.bzl", "next")

npm_link_all_packages(name = "node_modules")

_SRCS = [
    "//apps/hyd/app",
    "//apps/hyd/lib",
    "//apps/hyd/styles",
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

next(
    name = "next",
    srcs = _SRCS + [
        ":tailwind",
    ] + glob(
        [".env*"],
    ),
    data = [
        "next.config.ts",
        "tsconfig.json",
        ":node_modules/@tailwindcss/postcss",
        ":node_modules/autoprefixer",
        ":node_modules/next",
        ":node_modules/react",
        ":node_modules/react-dom",
        ":node_modules/tailwindcss",
        ":node_modules/typescript",
    ],
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
