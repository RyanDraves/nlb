load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("@pip//:requirements.bzl", "requirement")

py_binary(
    name = "wrapper",
    srcs = ["wrapper.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("inquirerpy"),
        requirement("rich-click"),
        "//nlb/util:console_utils",
        "//nlb/util:prompt_utils",
    ],
)
