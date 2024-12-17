def _patch_impl(name, visibility, src, out_file, patch, **kwargs):
    native.genrule(
        name = name,
        srcs = [src, patch],
        outs = [out_file],
        # `patch` will complain about the input file being read-only,
        # so route its complaints to /dev/null.
        cmd = "patch $$(readlink $(location {0})) -o $@ -i $(location {1}) --quiet 1>/dev/null".format(src, patch),
        visibility = visibility,
        **kwargs
    )

patch = macro(
    inherit_attrs = native.genrule,
    doc = "Apply patches to a file",
    implementation = _patch_impl,
    attrs = {
        "src": attr.label(
            mandatory = True,
            allow_single_file = True,
            doc = "The file to patch.",
            # Prevent receiving a `select` object on the input
            configurable = False,
        ),
        "out_file": attr.output(
            mandatory = True,
            doc = "The patched file.",
        ),
        "patch": attr.label(
            mandatory = True,
            allow_single_file = True,
            doc = "The patch file to apply.",
            # Prevent receiving a `select` object on the input
            configurable = False,
        ),
        "srcs": None,
        "outs": None,
        "cmd": None,
    },
)
