"""Rules for feature flags.

Graciously copied from
https://pigweed.dev/docs/blog/02-bazel-feature-flags.html#more-power-with-no-code-changes-platform-based-skylib-flags
"""

load("@bazel_skylib//rules:common_settings.bzl", "BuildSettingInfo")

def feature_cc_library(name, build_setting):
    hdrs_name = name + ".hdr"

    flag_header_file(
        name = hdrs_name,
        build_setting = build_setting,
    )

    native.cc_library(
        name = name,
        hdrs = [":" + hdrs_name],
    )

def _impl(ctx):
    out = ctx.actions.declare_file(ctx.attr.build_setting.label.name.lower() + ".hpp")

    # Convert boolean flags to canonical integer values.
    value = ctx.attr.build_setting[BuildSettingInfo].value
    if type(value) == type(True):
        if value:
            value = 1
        else:
            value = 0

    ctx.actions.write(
        output = out,
        content = r"""
#pragma once
#define {} {}
""".format(ctx.attr.build_setting.label.name.upper(), value),
    )
    return [DefaultInfo(files = depset([out]))]

flag_header_file = rule(
    implementation = _impl,
    attrs = {
        "build_setting": attr.label(
            doc = "Build setting (flag) to construct the header from.",
            mandatory = True,
        ),
    },
)
