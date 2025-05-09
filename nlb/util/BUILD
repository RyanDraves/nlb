load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:python.bzl", "py_binary", "py_test")

py_library(
    name = "click_utils",
    srcs = ["click_utils.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("rich-click"),
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

py_library(
    name = "dataclass",
    srcs = ["dataclass.py"],
    visibility = ["//visibility:public"],
    deps = [],
)

py_library(
    name = "exception",
    srcs = ["exception.py"],
    visibility = ["//visibility:public"],
    deps = [requirement("IPython")],
)

py_library(
    name = "introspection",
    srcs = ["introspection.py"],
    visibility = ["//visibility:public"],
)

py_test(
    name = "introspection_test",
    srcs = ["introspection_test.py"],
    deps = [
        ":introspection",
    ],
)

py_library(
    name = "path_utils",
    srcs = ["path_utils.py"],
    visibility = ["//visibility:public"],
    deps = [],
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
    name = "secrets",
    srcs = ["secrets.py"],
    visibility = ["//visibility:public"],
    deps = [":path_utils"],
)

py_library(
    name = "semantic_errors",
    srcs = ["semantic_errors.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("thefuzz"),
    ],
)

py_binary(
    name = "venv_completions",
    srcs = ["venv_completions.py"],
    visibility = ["//nlb:__pkg__"],
    deps = [
        requirement("rich-click"),
        requirement("inquirerpy"),
    ],
)
