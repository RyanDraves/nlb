load("@aspect_bazel_lib//lib:write_source_files.bzl", "write_source_file")
load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@rules_cc//cc:defs.bzl", "cc_library")

def buffham(name, srcs):
    native.filegroup(
        name = name,
        srcs = srcs,
    )

def buffham_py_library(name, bh, deps = []):
    """Generate a Python library from a Buffham file.

    Args:
        name: The name of the target.
        bh: The Buffham file to generate from.
        deps: Additional dependencies for the generated library.
    """
    basename = name.replace("_bh", "").replace("_py", "")

    native.genrule(
        name = name + "_gen",
        srcs = [bh],
        outs = [basename + "_bh.py"],
        cmd = "$(execpath //nlb/buffham) -l python -i $(location " + bh + ") -o $@",
        tools = ["//nlb/buffham"],
    )

    py_library(
        name = name,
        srcs = [basename + "_bh.py"],
        deps = deps + [
            "//emb/network/serialize:bh_cobs",
            "//emb/network/transport:transporter",
            "//nlb/buffham:bh",
        ],
    )

    native.genrule(
        name = name + "_pyi_gen",
        srcs = [bh],
        outs = [basename + "_bh.pyi.intermediate"],
        cmd = "$(execpath //nlb/buffham) -l python_stub -i $(location " + bh + ") -o $@",
        tools = ["//nlb/buffham"],
    )

    write_source_file(
        name = name + "_write",
        in_file = name + "_pyi_gen",
        out_file = basename + "_bh.pyi",
    )

def buffham_cc_library(name, bh, deps = []):
    """Generate a C++ library from a Buffham file.

    Args:
        name: The name of the target.
        bh: The Buffham file to generate from.
        deps: Additional dependencies for the generated library.
    """
    basename = name.replace("_bh", "").replace("_cc", "")

    native.genrule(
        name = name + "_gen",
        srcs = [bh],
        outs = [basename + "_bh.hpp"],
        cmd = "$(execpath //nlb/buffham) -l cpp -i $(location " + bh + ") -o $@",
        tools = ["//nlb/buffham"],
    )

    cc_library(
        name = name,
        hdrs = [basename + "_bh.hpp"],
        deps = deps + [
            "//emb/network/node:node_cc",
            "//emb/network/serialize:serializer_cc",
            "//emb/network/transport:transporter_cc",
        ],
    )
