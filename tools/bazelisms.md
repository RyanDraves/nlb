# Bazelisms

This short doc preserves some comments/code that was useful at one point, not needed now, but could easily be needed again when working with Bazel.

## Finding & using output groups

A target's provider may have different output groups. These are useful to use when one wants to depend on a subset of file outputs. A good example of this was getting the `picotool` binary from a `cmake` rule, which will always output many things and not just the binary.

Example:
```python
cmake(
    name = "picotool",
    ...
    out_binaries = ["picotool"],
)

filegroup(
    name = "picotool_bin",
    srcs = [":picotool"],
    # See https://stackoverflow.com/a/61282031 to list output_groups of a target;
    # this gets us just the final binary
    output_group = "picotool",
    visibility = ["//visibility:public"],
)
```
