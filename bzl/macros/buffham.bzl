"""Macros for generating Buffham files."""

load("@aspect_bazel_lib//lib:write_source_files.bzl", "write_source_file")
load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@rules_cc//cc:defs.bzl", "cc_library")

def _buffham_impl(name, visibility, src, deps, py, cc):
    native.filegroup(
        name = name,
        srcs = [src],
        visibility = visibility,
    )

    basename = name.replace("_bh", "")

    if py:
        cmd = "$(execpath //nlb/buffham) -l python -i $(location {0}) -o $(RULEDIR)/{1}_bh.py -s $(RULEDIR)/{1}_bh.pyi.intermediate".format(src, basename)
        for dep in deps:
            cmd += " --dep $(location {0})".format(dep)

        py_deps = [str(dep) + "_py" for dep in deps]

        native.genrule(
            name = name + "_py_gen",
            srcs = [src] + deps,
            outs = [basename + "_bh.py", basename + "_bh.pyi.intermediate"],
            cmd = cmd,
            tools = ["//nlb/buffham"],
            visibility = ["__pkg__"],
        )

        py_library(
            name = name + "_py",
            srcs = [basename + "_bh.py"],
            deps = py_deps + [
                "//emb/network/serialize:bh_cobs",
                "//emb/network/transport:transporter",
                "//nlb/buffham:bh",
            ],
            visibility = visibility,
        )

    if cc:
        cmd = "$(execpath //nlb/buffham) -l cpp -i $(location {0}) -o $(RULEDIR)/{1}_bh.hpp -s $(RULEDIR)/{1}_bh.cc".format(src, basename)
        for dep in deps:
            cmd += " --dep $(location {0})".format(dep)

        cc_deps = [str(dep) + "_cc" for dep in deps]

        native.genrule(
            name = name + "_cc_gen",
            srcs = [src] + deps,
            outs = [basename + "_bh.hpp", basename + "_bh.cc"],
            cmd = cmd,
            tools = ["//nlb/buffham"],
            visibility = ["__pkg__"],
        )

        cc_library(
            name = name + "_cc",
            hdrs = [basename + "_bh.hpp"],
            srcs = [basename + "_bh.cc"],
            deps = cc_deps + [
                "//emb/network/node:node_cc",
                "//emb/network/serialize:serializer_cc",
                "//emb/network/transport:transporter_cc",
            ],
            visibility = visibility,
        )

def _buffham_template_impl(name, visibility, bh, template, out_file, bh_deps, **kwargs):
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
        **kwargs
    )

def buffham_py_write(name, visibility = ["//visibility:public"]):
    """Legacy macro to write the generated `_bh.pyi` file to the source tree.

    `aspect_bazel_lib` needs to remove its `glob` call to make this a symbolic macro.
    """
    basename = name.replace("_bh", "").replace("_py", "").replace("_write", "")

    write_source_file(
        name = name,
        in_file = basename + "_bh.pyi.intermediate",
        out_file = basename + "_bh.pyi",
        suggested_update_target = "//:generate_bh",
        visibility = visibility,
    )

buffham = macro(
    implementation = _buffham_impl,
    doc = "Generate Buffham libraries from Buffham files",
    attrs = {
        "src": attr.label(
            mandatory = True,
            allow_single_file = True,
            doc = "The Buffham files to generate from.",
            # Prevent receiving a `select` object on the input
            configurable = False,
        ),
        "deps": attr.label_list(
            allow_files = True,
            doc = "Additional dependencies for the generated libraries.",
            # Prevent receiving a `select` object on the input
            configurable = False,
        ),
        "py": attr.bool(
            default = False,
            doc = "Whether to generate Python libraries.",
        ),
        "cc": attr.bool(
            default = False,
            doc = "Whether to generate C++ libraries.",
        ),
    },
)

buffham_template = macro(
    inherit_attrs = native.genrule,
    doc = "Generate a template from a Buffham file and a source file",
    implementation = _buffham_template_impl,
    attrs = {
        "bh": attr.label(
            mandatory = True,
            allow_single_file = True,
            doc = "The Buffham file to generate from.",
            # Prevent receiving a `select` object on the input
            configurable = False,
        ),
        "template": attr.label(
            mandatory = True,
            allow_single_file = True,
            doc = "The source file to generate the template from.",
            # Prevent receiving a `select` object on the input
            configurable = False,
        ),
        "out_file": attr.output(
            mandatory = True,
            doc = "The output file to write the template to.",
        ),
        "bh_deps": attr.label_list(
            allow_files = True,
            doc = "The transitive dependencies (currently necessary) of the Buffham file.",
            # Prevent receiving a `select` object on the input
            configurable = False,
        ),
        "srcs": None,
        "outs": None,
        "cmd": None,
        "tools": None,
    },
)
