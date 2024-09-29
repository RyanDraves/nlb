def patch(name, src, out_file, patch, visibility = ["//visibility:public"]):
    """Apply patches to a file.

    Args:
        name: The name of the target.
        src: The file to patch.
        out_file: The patched file.
        patch: The patch file to apply.
        visibility: The visibility of the patched file.
    """
    native.genrule(
        name = name,
        srcs = [src, patch],
        outs = [out_file],
        # `patch` will complain about the input file being read-only,
        # so route its complaints to /dev/null.
        cmd = "patch $$(readlink $(location {0})) -o $@ -i $(location {1}) --quiet 1>/dev/null".format(src, patch),
        visibility = visibility,
    )
