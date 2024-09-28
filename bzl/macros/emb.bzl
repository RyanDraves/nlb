# load("@aspect_bazel_lib//lib:run_binary.bzl", "run_binary")
load("@aspect_rules_py//py:defs.bzl", "py_binary")

def flash(name, binary, **kwargs):
    """Flash a binary to a device

    Args:
        name: The name of the binary
        binary: The binary to flash
        **kwargs: Additional arguments to pass to `run_binary`
    """
    # run_binary(
    #     name = name,
    #     srcs = [binary],
    #     args = [
    #         "$(location //emb/project/base:flash)",
    #         "$(location {0})".format(binary),
    #     ],
    #     mnemonic = "EmbFlash",
    #     tool = "//emb/project/base:flash",
    #     **kwargs
    # )

    # write_file(
    #     name = name + "_file",
    #     out = name + ".sh",
    #     content = [
    #         "#!/bin/bash",
    #         "$1 ${@:2}",
    #     ],
    # )

    # native.sh_binary(
    #     name = name,
    #     srcs = [name + ".sh"],
    #     data = ["//emb/project/base:flash", binary],
    #     args = [
    #         "$(location //emb/project/base:flash)",
    #         "$(location {0})".format(binary),
    #     ],
    # )

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
    )
