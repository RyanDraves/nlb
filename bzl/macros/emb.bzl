load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("//bzl/macros:python.bzl", "py_test")

def flash(name, binary, **kwargs):
    """Flash a binary to a device

    Args:
        name: The name of the binary
        binary: The binary to flash
        **kwargs: Additional arguments to pass to `py_binary`
    """
    py_binary(
        name = name,
        main = "//emb/project/base:flash.py",
        deps = [
            "//emb/project/base:flash",
        ],
        data = [binary],
        args = [
            "$(location {0})".format(binary),
        ],
        **kwargs
    )

def host_test(name, srcs, binary, deps, **kwargs):
    """Run a host test

    Args:
        name: The name of the binary
        srcs: The source files for the test
        binary: The binary to run
        deps: The dependencies for the test
        **kwargs: Additional arguments to pass to `py_binary`
    """
    py_test(
        name = name,
        srcs = srcs,
        deps = deps,
        data = [binary],
        env = {
            "HOST_BIN": "$(rootpath {0})".format(binary),
        },
        **kwargs
    )
