load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_binary", "py_test")

py_library(
    name = "punbox_design",
    srcs = ["punbox.py"],
    data = glob(
        ["lib/**"],
        exclude = ["lib/3d/**"],
    ),
    deps = [
        "//emb/project/punbox:punbox_bh_py",
        "@pip//skidl",
    ],
)

py_binary(
    name = "fab",
    srcs = ["fab.py"],
    add_completions = False,
    deps = [
        ":punbox_design",
        "@pip//rich_click",
        "@pip//skidl",
    ],
)

py_binary(
    name = "netlist",
    srcs = ["netlist.py"],
    add_completions = False,
    deps = [
        ":punbox_design",
        "@pip//skidl",
    ],
)

py_test(
    name = "punbox_test",
    srcs = ["punbox_test.py"],
    data = ["conftest.py"],
    deps = [
        ":punbox_design",
        "//emb/project/punbox:punbox_bh_py",
        "@pip//skidl",
    ],
)
