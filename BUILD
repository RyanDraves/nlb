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

# Usage:
#  - bazel run //:requirements.update
compile_pip_requirements(
    name = "requirements",
    src = "requirements.txt",
    requirements_txt = "requirements_lock.txt",
)

# Usage:
# - bazel run //:venv venv
py_venv(
    name = "venv",
    deps = all_requirements,
)

# Usage:
#  - Build all targets with flags
#    - bazel build --config pico //emb/...
#  - bazel run //:refresh_compile_commands
refresh_compile_commands(
    name = "refresh_compile_commands",

    # Specify the targets of interest.
    # For example, specify a dict of targets and any flags required to build.
    targets = {
        "//emb/...": "--config pico",
    },
)
