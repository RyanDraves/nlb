load("@aspect_bazel_lib//lib:write_source_files.bzl", "write_source_file")
load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@rules_cc//cc:defs.bzl", "cc_library")

def buffham(name, srcs, visibility = ["//visibility:public"]):
    native.filegroup(
        name = name,
        srcs = srcs,
        visibility = visibility,
    )

def buffham_py_library(name, bh, bh_deps = [], deps = [], visibility = ["//visibility:public"]):
    """Generate a Python library from a Buffham file.

    Args:
        name: The name of the target.
        bh: The Buffham file to generate from.
        bh_deps: The transitive dependencies (currently necessary) of the Buffham file.
        deps: Additional dependencies for the generated library.
        visibility: The visibility of the generated library.
    """
    basename = name.replace("_bh", "").replace("_py", "")

    cmd = "$(execpath //nlb/buffham) -l python -i $(location {0}) -o $(RULEDIR)/{1}_bh.py -s $(RULEDIR)/{1}_bh.pyi.intermediate".format(bh, basename)
    for dep in bh_deps:
        cmd += " --dep $(location {0})".format(dep)

    native.genrule(
        name = name + "_gen",
        srcs = [bh] + bh_deps,
        outs = [basename + "_bh.py", basename + "_bh.pyi.intermediate"],
        cmd = cmd,
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

    write_source_file(
        name = name + "_write",
        in_file = basename + "_bh.pyi.intermediate",
        out_file = basename + "_bh.pyi",
        suggested_update_target = "//:generate_bh",
        visibility = visibility,
    )

def buffham_cc_library(name, bh, bh_deps = [], deps = [], visibility = ["//visibility:public"]):
    """Generate a C++ library from a Buffham file.

    Args:
        name: The name of the target.
        bh: The Buffham file to generate from.
        bh_deps: The transitive dependencies (currently necessary) of the Buffham file.
        deps: Additional dependencies for the generated library.
        visibility: The visibility of the generated library.
    """
    basename = name.replace("_bh", "").replace("_cc", "")

    cmd = "$(execpath //nlb/buffham) -l cpp -i $(location {0}) -o $(RULEDIR)/{1}_bh.hpp -s $(RULEDIR)/{1}_bh.cc".format(bh, basename)
    for dep in bh_deps:
        cmd += " --dep $(location {0})".format(dep)

    native.genrule(
        name = name + "_gen",
        srcs = [bh] + bh_deps,
        outs = [basename + "_bh.hpp", basename + "_bh.cc"],
        cmd = cmd,
        tools = ["//nlb/buffham"],
    )

    cc_library(
        name = name,
        hdrs = [basename + "_bh.hpp"],
        srcs = [basename + "_bh.cc"],
        deps = deps + [
            "//emb/network/node:node_cc",
            "//emb/network/serialize:serializer_cc",
            "//emb/network/transport:transporter_cc",
        ],
        visibility = visibility,
    )

def buffham_template(name, bh, template, out_file, bh_deps = [], visibility = ["//visibility:public"]):
    """Generate a template from a Buffham file.

    Args:
        name: The name of the target.
        bh: The Buffham file to generate from.
        bh_deps: The transitive dependencies (currently necessary) of the Buffham file.
        template: The source file to generate the template from.
        out_file: The output file to write the template to.
        visibility: The visibility of the generated template.
    """
    cmd = "$(execpath //nlb/buffham) -l template -i $(location {0}) -t $(location {1}) -o $@".format(bh, template)
    for dep in bh_deps:
        cmd += " --dep $(location {0})".format(dep)

    native.genrule(
        name = name,
        srcs = [bh, template] + bh_deps,
        outs = [out_file],
        cmd = cmd,
        tools = ["//nlb/buffham"],
        visibility = visibility,
    )
