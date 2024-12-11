"""Perform a platform & linker script transition for a Pico binary.

Since we want to pick different values for the linker script within the same
platform, we need a custom rule that does both. I think. Please prove me wrong,
I hate writing these.
"""

def _transition():
    def _transition_impl(settings, attr):
        # buildifier: disable=unused-variable
        _ignore = settings
        return {
            "@pico-sdk//bazel/config:PICO_DEFAULT_LINKER_SCRIPT": attr.linker_script,
            "//command_line_option:platforms": str(attr.target_platform),
        }

    return transition(
        implementation = _transition_impl,
        inputs = [],
        outputs = [
            "@pico-sdk//bazel/config:PICO_DEFAULT_LINKER_SCRIPT",
            "//command_line_option:platforms",
        ],
    )

def _rule_impl(ctx):
    out = ctx.actions.declare_file(ctx.label.name)
    ctx.actions.symlink(output = out, is_executable = True, target_file = ctx.executable.binary)
    return [DefaultInfo(files = depset([out]), executable = out)]

pico_binary = rule(
    _rule_impl,
    attrs = {
        "binary": attr.label(
            doc = "Binary to transition",
            cfg = _transition(),
            executable = True,
            mandatory = True,
        ),
        "linker_script": attr.label(
            doc = "Linker script to transition to",
            mandatory = True,
        ),
        "target_platform": attr.label(
            doc = "Target platform to transition to",
            mandatory = True,
        ),
    },
)
