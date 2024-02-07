# load("@aspect_rules_py//py:defs.bzl", "py_venv")
load("@rules_pyvenv//:venv.bzl", "py_venv")
load("@buildifier_prebuilt//:rules.bzl", "buildifier")
load("@pip//:requirements.bzl", "all_requirements")
load("@rules_python//python:pip.bzl", "compile_pip_requirements")

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
