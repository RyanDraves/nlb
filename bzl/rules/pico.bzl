# @pico-sdk rule wrapper, based on:
# https://github.com/antmicro/pigweed/blob/c9d5bef2f82612fa8d4be0d53b614bbc02bab62b/targets/rp2040/transition.bzl
# https://github.com/dfr/rules_pico/blob/main/pico/defs.bzl#L322

RP2040_FLAGS = {
    "@pico-sdk//bazel/config:PICO_STDIO_UART": False,
    "@pico-sdk//bazel/config:PICO_STDIO_USB": True,
    "@pico-sdk//bazel/config:PICO_STDIO_SEMIHOSTING": False,
    "//command_line_option:platforms": "@pico-sdk//bazel/platform:rp2040",
}

def _rp2040_transition():
    def _rp2040_transition_impl(settings, attr):
        # buildifier: disable=unused-variable
        _ignore = settings
        overrides = {}
        if hasattr(attr, "stdio_uart"):
            overrides["@pico-sdk//bazel/config:PICO_STDIO_UART"] = attr.stdio_uart
        if hasattr(attr, "stdio_usb"):
            overrides["@pico-sdk//bazel/config:PICO_STDIO_USB"] = attr.stdio_usb
        if hasattr(attr, "stdio_semihosting"):
            overrides["@pico-sdk//bazel/config:PICO_STDIO_SEMIHOSTING"] = attr.stdio_semihosting
        return RP2040_FLAGS | overrides

    return transition(
        implementation = _rp2040_transition_impl,
        inputs = [],
        outputs = RP2040_FLAGS.keys(),
    )

def _rp2040_elf_impl(ctx):
    out = ctx.actions.declare_file(ctx.label.name)
    ctx.actions.symlink(output = out, is_executable = True, target_file = ctx.executable.binary)
    return [DefaultInfo(files = depset([out]), executable = out)]

def _rp2040_binary_impl(ctx):
    # I can't figure out why this is a sequence, but we're expecting one element
    binary = ctx.attr.binary[0]

    out = ctx.actions.declare_file(ctx.label.name)
    ctx.actions.symlink(output = out, is_executable = False, target_file = binary.files.to_list()[0])
    return [DefaultInfo(files = depset([out]))]

rp2040_elf = rule(
    _rp2040_elf_impl,
    attrs = {
        "binary": attr.label(
            doc = "cc_binary to build for the rp2040",
            cfg = _rp2040_transition(),
            executable = True,
            mandatory = True,
        ),
        "stdio_usb": attr.bool(
            doc = "Set to true to enable stdio output over USB",
            default = True,
        ),
        "stdio_uart": attr.bool(
            doc = "Set to true to enable stdio output over UART",
            default = False,
        ),
        "stdio_semihosting": attr.bool(
            doc = "Set to true to enable stdio output via debugger",
            default = False,
        ),
        "_allowlist_function_transition": attr.label(
            default = "@bazel_tools//tools/allowlists/function_transition_allowlist",
        ),
    },
)

rp2040_binary = rule(
    _rp2040_binary_impl,
    attrs = {
        "binary": attr.label(
            doc = ".bin file from `objcopy` to generate for the rp2040",
            cfg = _rp2040_transition(),
            executable = False,
            mandatory = True,
        ),
    },
)
