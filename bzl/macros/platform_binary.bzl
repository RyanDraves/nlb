load("@bazel_skylib//rules:select_file.bzl", "select_file")
load("@rules_platform//platform_data:defs.bzl", "platform_data")

def platform_binary(name, binary, platform, **kwargs):
    """Platform transition a binary target

    `platform_data` is the `rules_platform` way of doing what `//bzl/rules:platform_transition`
    does, but for executable targets. It seems to include extra files - runfiles maybe - so this
    macro gives the rule a better name and plucks the desired output file.

    Args:
        name: The name of the target
        binary: The binary target to transition
        platform: The platform to transition to
        **kwargs: Additional arguments to pass
    """

    platform_data(
        name = name + "_intermediate",
        platform = platform,
        target = binary,
    )
    select_file(
        name = name,
        srcs = name + "_intermediate",
        subpath = name + "_intermediate",
        visibility = ["//visibility:public"],
        **kwargs
    )
