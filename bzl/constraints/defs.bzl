# Graciously copied from the pico-sdk
# https://github.com/raspberrypi/pico-sdk/blob/95ea6acad131124694cda1c162c52cd30e0aece0/bazel/defs.bzl#L62-L80
#
# Currently unused, but a convenient helper to keep around

# Because the syntax for target_compatible_with when used with config_setting
# rules is both confusing and verbose, provide some helpers that make it much
# easier and clearer to express compatibility.
#
# Context: https://github.com/bazelbuild/bazel/issues/12614

def compatible_with_config(config_label):
    """Expresses compatibility with a config_setting."""
    return select({
        config_label: [],
        "//conditions:default": ["@platforms//:incompatible"],
    })

def incompatible_with_config(config_label):
    """Expresses incompatibility with a config_setting."""
    return select({
        config_label: ["@platforms//:incompatible"],
        "//conditions:default": [],
    })
