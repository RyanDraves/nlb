"""Bazel rule to transition a target to a different platform.
Example:
platform_transition(
    name = "my_library",
    dep = [":my_library_that_needs_a_custom_toolchain"],
    platform = "//my_platform:my_platform",
)
Inspired by https://stackoverflow.com/a/77020123 and
https://stackoverflow.com/a/71179440
"""

def _impl(_, attrs):
    return {"//command_line_option:platforms": str(attrs.platform)}

_platform_transition_impl = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:platforms"],
)

def _rule_impl(ctx):
    # I can't figure out why this is a sequence, but we're expecting one element
    dep = ctx.attr.dep[0]

    providers = []
    if DefaultInfo in dep:
        providers.append(dep[DefaultInfo])
    if CcInfo in dep:
        providers.append(dep[CcInfo])
    return providers

platform_transition = rule(
    implementation = _rule_impl,
    attrs = {
        "_allowlist_function_transition": attr.label(
            default = "@bazel_tools//tools/allowlists/function_transition_allowlist",
        ),
        "dep": attr.label(cfg = _platform_transition_impl),
        "platform": attr.label(),
    },
)
