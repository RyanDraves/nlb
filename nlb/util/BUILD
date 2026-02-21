load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@rules_go//go:def.bzl", "go_library")
load("//bzl/macros:python.bzl", "py_binary", "py_test")

py_library(
    name = "click_utils",
    srcs = ["click_utils.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//rich_click",
    ],
)

py_library(
    name = "console_utils",
    srcs = ["console_utils.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//rich",
    ],
)

py_library(
    name = "dataclass",
    srcs = ["dataclass.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "dataframe",
    srcs = ["dataframe.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":dataclass",
        "@pip//pandas",
    ],
)

py_library(
    name = "exception",
    srcs = ["exception.py"],
    visibility = ["//visibility:public"],
    deps = ["@pip//ipython"],
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
)

py_library(
    name = "prompt_utils",
    srcs = ["prompt_utils.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//prompt_toolkit",
    ],
)

py_library(
    name = "semantic_errors",
    srcs = ["semantic_errors.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//thefuzz",
    ],
)

py_library(
    name = "timeout",
    srcs = ["timeout.py"],
    visibility = ["//visibility:public"],
)

py_test(
    name = "timeout_test",
    srcs = ["timeout_test.py"],
    deps = [
        ":timeout",
    ],
)

py_library(
    name = "timer",
    srcs = ["timer.py"],
    visibility = ["//visibility:public"],
)

py_binary(
    name = "venv_completions",
    srcs = ["venv_completions.py"],
    visibility = ["//nlb:__pkg__"],
    deps = [
        "@pip//inquirerpy",
        "@pip//rich_click",
    ],
)

genrule(
    name = "version_gen",
    outs = ["version.py"],
    cmd = "$(execpath :version.sh) bazel-out/stable-status.txt $(location version.py)",
    stamp = -1,
    tools = [":version.sh"],
)

py_library(
    name = "version",
    srcs = ["version.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "test_utils",
    srcs = ["test_utils.py"],
    visibility = ["//visibility:public"],
)

go_library(
    name = "util",
    srcs = [
        "console.go",
        "prompt.go",
    ],
    importpath = "nlb/nlb/util",
    visibility = ["//visibility:public"],
    deps = [
        "@com_github_charmbracelet_bubbles//filepicker",
        "@com_github_charmbracelet_bubbles//textinput",
        "@com_github_charmbracelet_bubbletea//:bubbletea",
        "@com_github_charmbracelet_lipgloss//:lipgloss",
    ],
)
