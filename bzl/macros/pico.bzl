load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_filegroup")
load("@pico-sdk//bazel/toolchain:objcopy.bzl", "objcopy_to_bin")
load("@rules_cc//cc:defs.bzl", "cc_binary", "cc_library")
load("//bzl/macros:emb.bzl", "flash")
load("//bzl/rules:pico.bzl", "pico_binary")

def _pico_elf_and_bin(name, binary, platform, linker_script, **kwargs):
    """Macro for the ELF and bin files for a Pico project

    Args:
        name: The name of the project
        binary: The binary to use
        platform: The Pico platform to build for
        linker_script: The linker script to use
        **kwargs: Additional arguments to pass to `rp2040_binary`
    """
    pico_binary(
        name = name + ".elf",
        binary = binary,
        target_platform = platform,
        linker_script = linker_script,
    )

    # `_intermediate` as it doesn't have the right platform
    objcopy_to_bin(
        name = name + "_bin_intermediate",
        src = name + ".elf",
        out = name + "_intermediate.bin",
        target_compatible_with = ["@pico-sdk//bazel/constraint:rp2040"],
    )

    platform_transition_filegroup(
        name = name + ".bin",
        srcs = [name + "_bin_intermediate"],
        target_platform = platform,
        **kwargs
    )

def pico_project(name, srcs, deps, platform = "//bzl/platforms:rp2040", linker_script = "//emb/project/bootloader:application_linker_script", **kwargs):
    """Compile a Pico project

    Produces a host binary, an ELF file, a UF2 file, and a bin file.

    The UF2 file can be flashed to a Pico device in BOOTSEL mode with:
    ```
    bazel run //tools:picotool -- load bazel-bin/path/to/name.uf2
    ```

    Args:
        name: The name of the project
        srcs: The source files
        deps: The dependencies
        platform: The Pico platform to build for
        linker_script: The linker script to use
        **kwargs: Additional arguments to pass to binary targets
    """
    name = name.replace("_pico", "")

    cc_binary(
        name = name,
        srcs = srcs,
        deps = deps,
        **kwargs
    )

    _pico_elf_and_bin(name, name, platform, linker_script, **kwargs)

    # Create an additional binary without the bootloader in the linker script
    _pico_elf_and_bin(
        name + "_no_bootloader",
        name,
        platform,
        "@pico-sdk//src/rp2_common/pico_crt0:default_linker_script",
        tags = ["manual"],
        **kwargs
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

    # Add a target to flash the binary
    flash(
        name = name + "_flash",
        binary = name + ".bin",
    )

def pio_cc_library(name, pio, hdrs = [], **kwargs):
    """Compile a PIO C++ library

    Args:
        name: The name of the library
        pio: The PIO assembly file
        hdrs: Additional headers to include
        **kwargs: Additional arguments to pass to `cc_library`
    """
    native.genrule(
        name = name + "_gen",
        srcs = [pio],
        outs = [pio + ".h"],
        # -v 0 corresponds to the version 0 of the PIO, which is the RP2040
        cmd = "$(execpath @pioasm//:pioasm) -o c-sdk -v 0 $(location {}) $(location {})".format(pio, pio + ".h"),
        tools = ["@pioasm//:pioasm"],
    )

    cc_library(
        name = name,
        # The platform-specific PIO header is always included; it's innocuous if it's not used
        hdrs = [pio + ".h"] + hdrs,
        # This CC library explicitly does not call out its `@pico-sdk//src/rp2_common/hardware_pio` dependency;
        # the caller of this macro should add it to the Pico select on the `deps` attribute.
        **kwargs
    )
