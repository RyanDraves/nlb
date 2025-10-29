"""Macros for Python"""

load("@aspect_rules_py//py:defs.bzl", _py_binary = "py_binary", _py_test = "py_test")
load("@pip//:requirements.bzl", "requirement")

def py_test(name, srcs, deps = [], args = [], **kwargs):
    """py_test wrapper to invoke pytest

    The default behavior is to require the test file to make its
    own `__main__` or it'll silently pass.

    Setup via https://stackoverflow.com/a/67389568
    """
    _py_test(
        name = name,
        srcs = srcs + ["//bzl/macros:pytest_wrapper.py"],
        # The `_determine_main` finds a matching subpath, so we pass
        # a substring of the path instead of a label. Ew.
        main = "pytest_wrapper.py",
        deps = deps + [
            requirement("pytest"),
        ],
        args = args + ["$(location :%s)" % src for src in srcs],
        **kwargs
    )

def py_binary(name, add_completions = True, **kwargs):
    """py_binary wrapper to add bash completion"""
    _py_binary(
        name = name,
        **kwargs
    )

    if add_completions:
        # Follow `click`'s shell completion guide:
        # https://click.palletsprojects.com/en/stable/shell-completion/
        # Note that Python binaries will want to set
        # `entry_point_func(prog_name='{name}')` so click recognizes the
        # request for completions in Bazel settings. `{name}` should also
        # be the name of the `console_scripts` entry in the wheel.
        native.genrule(
            name = name + "_completions",
            outs = ["{}-completion.bash".format(name)],
            cmd = "_{0}_COMPLETE=bash_source $(execpath :{1}) > $(@D)/{2}-completion.bash".format(name.upper(), name, name),
            tools = [":{}".format(name)],
            visibility = ["//visibility:public"],
        )
