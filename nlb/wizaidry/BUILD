load("@aspect_rules_py//py:defs.bzl", "py_library")

# Visible for PyPI publishing
package(default_visibility = ["//nlb:__pkg__"])

py_library(
    name = "audio_util",
    srcs = ["audio_util.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//numpy",
        "@pip//pyaudio",
        "@pip//pydub",
        "@pip//sounddevice",
    ],
)

py_library(
    name = "text_handler",
    srcs = ["text_handler.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":util",
        "//nlb/mcp:tool_manager",
        "//nlb/util:console_utils",
        "@pip//inquirerpy",
        "@pip//openai",
    ],
)

py_library(
    name = "util",
    srcs = ["util.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//nlb/util:introspection",
        "@pip//openai",
    ],
)

py_library(
    name = "voice_handler",
    srcs = ["voice_handler.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":audio_util",
        ":util",
        "//nlb/mcp:tool_manager",
        "//nlb/util:console_utils",
        "@pip//openai",
        "@pip//pynput",
        "@pip//rich",
        "@pip//sounddevice",
    ],
)
