load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_binary", "py_test")

py_library(
    name = "punbox",
    srcs = ["punbox.py"],
    data = glob(
        ["lib/**"],
        exclude = ["lib/3d/**"],
    ),
    visibility = ["//visibility:public"],
    deps = [
        "//emb/project/punbox:punbox_bh_py",
        "@pip//skidl",
    ],
)

py_binary(
    name = "fab",
    srcs = ["fab.py"],
    add_completions = False,
    visibility = ["//visibility:public"],
    deps = [
        ":punbox",
        "@pip//rich_click",
    ],
)

py_binary(
    name = "netlist",
    srcs = ["netlist.py"],
    add_completions = False,
    visibility = ["//visibility:public"],
    deps = [
        ":punbox",
        "@pip//skidl",
    ],
)

py_test(
    name = "punbox_test",
    srcs = ["punbox_test.py"],
    deps = [
        ":conftest",
        ":punbox",
        "//emb/project/punbox:punbox_bh_py",
        "@pip//skidl",
    ],
)

py_library(
    name = "conftest",
    testonly = True,
    srcs = ["conftest.py"],
    visibility = ["//visibility:public"],
)
