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

## Platforms transitions

Multi-platform builds require a platform transition on the targets to be built for other platforms. There are a few competing rules to be the "generic rule that implements a platform transition".

The current state of affairs is:
- [rules_platform](https://registry.bazel.build/modules/rules_platform)'s `platform_data` (binary targets only)
- [aspect_bazel_lib](https://github.com/bazel-contrib/bazel-lib/blob/main/docs/transitions.md)'s `transitions.bzl` (binary targets, file targets, test targets)
- `//bzl/rules:platform_transition.bzl` (file targets, CC libraries)

It's a complete mess. If you want to customize flags within a platform, instead of binding all of them to the platform with platform flags, then custom rules for that are needed too.

## Using Ruby / Bundle binaries

If I (or anyone reading this) need to run a Ruby/Bundle/whatever binary as part of a build process, [jekyll.bzl](https://github.com/RyanDraves/nlb/blob/5bfad07ffbd7fbf1a0fd087b260b148b7e0f655f/bzl/macros/jekyll.bzl) implemented this.
