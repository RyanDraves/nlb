"""Bazel rule to transition a non-executable target to a different platform.

This rule also exposes `CCInfo` for CC target transitions.

Example:
platform_transition(
    name = "my_library",
    dep = [":my_library_that_needs_a_custom_toolchain"],
    target_platform = "//my_platform:my_platform",
)
Inspired by https://stackoverflow.com/a/77020123 and
https://stackoverflow.com/a/71179440
"""

def _impl(_, attrs):
    return {"//command_line_option:platforms": str(attrs.target_platform)}

_platform_transition_impl = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:platforms"],
)

def _rule_impl(ctx):
    dep = ctx.attr.dep

    providers = []
    if DefaultInfo in dep:
        providers.append(dep[DefaultInfo])
    if CcInfo in dep:
        providers.append(dep[CcInfo])
    return providers

platform_transition = rule(
    implementation = _rule_impl,
    cfg = _platform_transition_impl,
    attrs = {
        "_allowlist_function_transition": attr.label(
            default = "@bazel_tools//tools/allowlists/function_transition_allowlist",
        ),
        "dep": attr.label(mandatory = True),
        "target_platform": attr.label(mandatory = True),
    },
)
