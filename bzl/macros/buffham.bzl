load("@aspect_bazel_lib//lib:write_source_files.bzl", "write_source_file")
load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@rules_cc//cc:defs.bzl", "cc_library")

def buffham(name, srcs):
    native.filegroup(
        name = name,
        srcs = srcs,
    )

def buffham_py_library(name, bh, deps = [], visibility = ["//visibility:public"]):
    """Generate a Python library from a Buffham file.

    Args:
        name: The name of the target.
        bh: The Buffham file to generate from.
        deps: Additional dependencies for the generated library.
        visibility: The visibility of the generated library.
    """
    basename = name.replace("_bh", "").replace("_py", "")

    native.genrule(
        name = name + "_gen",
        srcs = [bh],
        outs = [basename + "_bh.py"],
        cmd = "$(execpath //nlb/buffham) -l python -i $(location {0}) -o $@".format(bh),
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
        visibility = visibility,
    )

    native.genrule(
        name = name + "_pyi_gen",
        srcs = [bh],
        outs = [basename + "_bh.pyi.intermediate"],
        cmd = "$(execpath //nlb/buffham) -l python_stub -i $(location {0}) -o $@".format(bh),
        tools = ["//nlb/buffham"],
    )

    write_source_file(
        name = name + "_write",
        in_file = name + "_pyi_gen",
        out_file = basename + "_bh.pyi",
        suggested_update_target = "//:generate_bh",
        visibility = visibility,
    )

def buffham_cc_library(name, bh, deps = [], visibility = ["//visibility:public"]):
    """Generate a C++ library from a Buffham file.

    Args:
        name: The name of the target.
        bh: The Buffham file to generate from.
        deps: Additional dependencies for the generated library.
        visibility: The visibility of the generated library.
    """
    basename = name.replace("_bh", "").replace("_cc", "")

    native.genrule(
        name = name + "_gen",
        srcs = [bh],
        outs = [basename + "_bh.hpp"],
        cmd = "$(execpath //nlb/buffham) -l cpp -i $(location {0}) -o $@".format(bh),
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
        visibility = visibility,
    )

def buffham_template(name, bh, template, out_file, visibility = ["//visibility:public"]):
    """Generate a template from a Buffham file.

    Args:
        name: The name of the target.
        bh: The Buffham file to generate from.
        template: The source file to generate the template from.
        out_file: The output file to write the template to.
        visibility: The visibility of the generated template.
    """
    native.genrule(
        name = name,
        srcs = [bh, template],
        outs = [out_file],
        cmd = "$(execpath //nlb/buffham) -l template -i $(location {0}) -t $(location {1}) -o $@".format(bh, template),
        tools = ["//nlb/buffham"],
    )
