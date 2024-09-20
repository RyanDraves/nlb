load("@pico-sdk//bazel/toolchain:objcopy.bzl", "objcopy_to_bin")
load("@rules_cc//cc:defs.bzl", "cc_binary")
load("//bzl/rules:pico.bzl", "rp2040_binary", "rp2040_elf")

def pico_project(name, srcs, deps):
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
    """
    cc_binary(
        name = name,
        srcs = srcs,
        deps = deps,
    )

    # Apply transitions to the `rp2040` configuration
    rp2040_elf(
        name = name + ".elf",
        binary = name,
        stdio_uart = False,
        stdio_usb = True,
        stdio_semihosting = False,
    )

    # `_intermediate` as it doesn't have the right platform
    objcopy_to_bin(
        name = name + "_bin_intermediate",
        src = name + ".elf",
        out = name + "intermediate.bin",
        target_compatible_with = ["@pico-sdk//bazel/constraint:rp2040"],
    )
    rp2040_binary(
        name = name + ".bin",
        binary = name + "_bin_intermediate",
    )

    # Generate a UF2 file from the ELF file
    # Adapted from https://github.com/raspberrypi/pico-sdk/blob/efe2103f9b28458a1615ff096054479743ade236/tools/uf2_aspect.bzl
    native.genrule(
        name = name + "_uf2",
        srcs = [name + ".elf"],
        outs = [name + ".uf2"],
        cmd = "$(execpath @picotool//:picotool) uf2 convert --quiet -t elf $(location {}.elf) $(location {}.uf2)".format(name, name),
        tools = ["@picotool//:picotool"],
    )
