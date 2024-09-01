load("@aspect_rules_py//py:defs.bzl", _py_test = "py_test")
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
        main = "//bzl/macros:pytest_wrapper.py",
        deps = deps + [
            requirement("pytest"),
        ],
        args = args + ["$(location :%s)" % src for src in srcs],
        **kwargs
    )
