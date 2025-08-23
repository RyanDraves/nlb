load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:python.bzl", "py_binary")

py_library(
    name = "__init__",
    srcs = ["__init__.py"],
    deps = [
        ":st",
    ],
)

py_library(
    name = "interface",
    srcs = ["interface.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("marshmallow_dataclass"),
    ],
)

py_library(
    name = "st",
    srcs = ["st.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":interface",
    ],
)

py_binary(
    name = "sharetrace_demo",
    srcs = ["sharetrace_demo.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("rich-click"),
        ":st",
        "//nlb/util:click_utils",
    ],
)

py_binary(
    name = "sharetrace",
    srcs = ["sharetrace.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("inquirerpy"),
        requirement("jinja2"),
        requirement("pygments"),
        requirement("rich-click"),
        ":interface",
        "//nlb/util:console_utils",
    ],
)
