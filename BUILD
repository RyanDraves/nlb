load("@buildifier_prebuilt//:rules.bzl", "buildifier")
load("@hedron_compile_commands//:refresh_compile_commands.bzl", "refresh_compile_commands")
load("@pip//:requirements.bzl", "all_requirements")
load("@rules_python//python:pip.bzl", "compile_pip_requirements")
load("@rules_pyvenv//:venv.bzl", "py_venv")

package(default_visibility = ["//visibility:public"])

buildifier(
    name = "buildifier.check",
    diff_command = "diff -u",
    lint_mode = "warn",
    mode = "diff",
)

buildifier(
    name = "buildifier.fix",
    lint_mode = "fix",
    mode = "fix",
)

compile_pip_requirements(
    name = "requirements",
    src = "requirements.txt",
    requirements_txt = "requirements_lock.txt",
)

py_venv(
    name = "venv",
    deps = all_requirements,
)

refresh_compile_commands(
    name = "refresh_compile_commands",

    # Specify the targets of interest.
    # For example, specify a dict of targets and any flags required to build.
    targets = {
        "//emb/...": "--config pico",
    },
    # No need to add flags already in .bazelrc. They're automatically picked up.
    # If you don't need flags, a list of targets is also okay, as is a single target string.
    # Wildcard patterns, like //... for everything, *are* allowed here, just like a build.
    # As are additional targets (+) and subtractions (-), like in bazel query https://docs.bazel.build/versions/main/query.html#expressions
    # And if you're working on a header-only library, specify a test or binary target that compiles it.
)
