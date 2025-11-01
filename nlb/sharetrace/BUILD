load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_binary")

py_library(
    name = "__init__",
    srcs = ["__init__.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "interface",
    srcs = ["interface.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//marshmallow_dataclass",
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
        ":st",
        "//nlb/util:click_utils",
        "@pip//rich_click",
    ],
)

py_binary(
    name = "sharetrace",
    srcs = ["sharetrace.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":interface",
        "//nlb/util:console_utils",
        "@pip//inquirerpy",
        "@pip//jinja2",
        "@pip//pygments",
        "@pip//rich_click",
    ],
)
