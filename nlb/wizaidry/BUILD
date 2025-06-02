load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")

# Visible for PyPI publishing
package(default_visibility = ["//nlb:__pkg__"])

py_library(
    name = "audio_util",
    srcs = ["audio_util.py"],
    deps = [
        requirement("numpy"),
        requirement("pyaudio"),
        requirement("pydub"),
        requirement("sounddevice"),
    ],
)

py_library(
    name = "text_handler",
    srcs = ["text_handler.py"],
    deps = [
        "//nlb/mcp:tool_manager",
        ":util",
        "//nlb/util:console_utils",
        requirement("openai"),
    ],
)


py_library(
    name = "util",
    srcs = ["util.py"],
    deps = [
        "//nlb/util:introspection",
        requirement("openai"),
    ],
)

py_library(
    name = "voice_handler",
    srcs = ["voice_handler.py"],
    deps = [
        ":audio_util",
        "//nlb/mcp:tool_manager",
        ":util",
        "//nlb/util:console_utils",
        requirement("openai"),
        requirement("pynput"),
        requirement("rich"),
        requirement("sounddevice"),
    ],
)
