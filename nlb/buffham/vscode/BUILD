load("@aspect_rules_js//js:defs.bzl", "js_run_binary")
load("@bazel_skylib//rules:build_test.bzl", "build_test")
load("@npm//:defs.bzl", "npm_link_all_packages")
load("@npm//nlb/buffham/vscode:@vscode/vsce/package_json.bzl", vsce_bin = "bin")

npm_link_all_packages(name = "node_modules")

vsce_bin.vsce_binary(
    name = "vsce",
    visibility = ["//visibility:private"],
)

js_run_binary(
    name = "vsix",
    srcs = [
        ".vscodeignore",
        "LICENSE.md",
        "README.md",
        "language-configuration.json",
        "package.json",
        "snippets/buffham.json",
        "syntaxes/buffham.tmLanguage.json",
        # vsce's secretlint scan resolves its rule modules with a node_modules
        # walk-up from the package store; they're hoisted to the root in
        # MODULE.bazel so the resolution succeeds
        "//:node_modules/@secretlint/secretlint-formatter-sarif",
        "//:node_modules/@secretlint/secretlint-rule-no-dotenv",
        "//:node_modules/@secretlint/secretlint-rule-preset-recommend",
    ],
    args = [
        "package",
        # The extension is declarative (no runtime deps); skip vsce's `npm` invocation
        "--no-dependencies",
        "-o",
        "buffham.vsix",
    ],
    chdir = package_name(),
    outs = ["buffham.vsix"],
    tool = ":vsce",
    visibility = ["//visibility:public"],
)

build_test(
    name = "vsix_build_test",
    targets = [":vsix"],
)
