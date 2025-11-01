load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_binary", "py_test")

py_binary(
    name = "arduino_mcp",
    srcs = ["arduino_mcp.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":arduino",
        "@pip//fastmcp",
        "@pip//rich_click",
    ],
)

py_library(
    name = "arduino",
    srcs = ["arduino.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":util",
        "//nlb/arduino:client",
        "@pip//fastmcp",
        "@pip//pydantic",
    ],
)

py_binary(
    name = "file_edit_mcp",
    srcs = ["file_edit_mcp.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":file_edit",
        "@pip//fastmcp",
        "@pip//rich_click",
    ],
)

py_test(
    name = "file_edit_test",
    srcs = ["file_edit_test.py"],
    deps = [
        ":file_edit",
        "@pip//fastmcp",
    ],
)

py_library(
    name = "file_edit",
    srcs = ["file_edit.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":util",
        "//nlb/util:semantic_errors",
        "@pip//fastmcp",
        "@pip//pydantic",
    ],
)

py_library(
    name = "tool_manager",
    srcs = ["tool_manager.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "util",
    srcs = ["util.py"],
    visibility = ["//visibility:public"],
)
