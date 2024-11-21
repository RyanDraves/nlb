load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")

py_library(
    name = "click_utils",
    srcs = ["click_utils.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("rich-click"),
    ],
)

py_library(
    name = "dataclass",
    srcs = ["dataclass.py"],
    visibility = ["//visibility:public"],
    deps = [
    ],
)

py_library(
    name = "prompt_utils",
    srcs = ["prompt_utils.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("prompt_toolkit"),
    ],
)

py_library(
    name = "console_utils",
    srcs = ["console_utils.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("rich"),
    ],
)
