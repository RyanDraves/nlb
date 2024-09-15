load("@rules_cc//cc:defs.bzl", "cc_binary")
load("@rules_pico//pico:defs.bzl", "pico_add_uf2_output", "pico_binary", "pico_build_with_config")

def pico_project(name, srcs, deps, include_host = True):
    """Compile a Pico project

    Produces a host binary, an ELF file, a UF2 file, a binary file, and a map.
    Everything but the host binary is compiled with `--config pico`.

    The UF2 file can be flashed to a Pico device in BOOTSEL mode with:
    ```
    bazel run //tools:picotool -- load bazel-bin/path/to/name.uf2
    ```

    Args:
        name: The name of the project
        srcs: The source files
        deps: The dependencies
        include_host: Whether to include the host binary (default: True)
    """
    name = name.replace("_pico", "")

    if include_host:
        # Host compilation of the binary
        cc_binary(
            name = name + "_host",
            srcs = srcs,
            deps = deps,
        )

    # Pico compilation of the binary;
    # compiled with `--config pico`
    pico_binary(
        name = name + ".elf",
        srcs = srcs,
        deps = deps,
    )

    # Enable stdio over USB
    pico_build_with_config(
        name = name + "_usb.elf",
        input = name + ".elf",
        stdio_uart = False,
        stdio_usb = True,
    )

    # TODO: File ticket for pico_add_bin_output & pico_add_map_output back at
    # bazel-arm-none-eabi; the toolchain executable paths are wrong and I
    # couldn't figure it out after a couple hours.
    native.genrule(
        name = name + "_bin",
        srcs = [name + "_usb.elf"],
        outs = [name + ".bin"],
        cmd = "$(execpath @arm_none_eabi//:objcopy) -O binary $< $@",
        tools = ["@arm_none_eabi//:objcopy"],
    )

    native.genrule(
        name = name + "_map",
        srcs = [name + "_usb.elf"],
        outs = [name + ".map"],
        cmd = "$(execpath @arm_none_eabi//:objdump) -C --all-headers $< > $@",
        tools = ["@arm_none_eabi//:objdump"],
    )

    pico_add_uf2_output(
        name = name + ".uf2",
        input = name + "_usb.elf",
    )
