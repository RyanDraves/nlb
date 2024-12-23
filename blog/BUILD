load("@aspect_rules_js//js:defs.bzl", "js_library", "js_test")
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

filegroup(
    name = "posts",
    srcs = glob(["_posts/*.mdx"]),
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
        ":node_modules/@types/react",
    ],
)

next(
    name = "next",
    srcs = _SRCS + [
        ":tailwind",
    ],
    data = [
        "next.config.ts",
        "package.json",
        "tsconfig.json",
        ":node_modules/autoprefixer",
        ":node_modules/next",
        ":node_modules/postcss",
        ":node_modules/react",
        ":node_modules/react-dom",
        ":node_modules/tailwindcss",
        ":node_modules/typescript",
        ":posts",
    ],
    next_bin = "./node_modules/next/dist/bin/next",
    next_js_binary = ":next_js_binary",
)

# A smoke test on the artifact produced by the :next target
js_test(
    name = "build_smoke_test",
    chdir = package_name(),
    data = [":next"],
    entry_point = "build_smoke_test.js",
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

js_library(
    name = "package_json",
    srcs = ["package.json"],
    visibility = ["//visibility:public"],
)

js_library(
    name = "jest_config",
    srcs = ["jest.config.js"],
    visibility = ["//visibility:public"],
    deps = [":node_modules/next"],
)

js_library(
    name = "eslintrc",
    srcs = [".eslintrc.js"],
    visibility = ["//:__subpackages__"],
    deps = [
        ":node_modules/@next/eslint-plugin-next",
        ":node_modules/eslint-config-next",
    ],
)

build_test(
    name = "build_test",
    targets = [
        ":next",
        # Not build testing the `:next_export` target since this `next export` writes back to the `.next` directory which
        # causes issues with trying to write to an input. See https://github.com/vercel/next.js/issues/43344.
        # TODO: fix in Next.js (https://github.com/vercel/next.js/issues/43344) or find work-around.
        # ":next_export",
    ],
)
