load("@aspect_rules_py//py:defs.bzl", "py_binary")

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
