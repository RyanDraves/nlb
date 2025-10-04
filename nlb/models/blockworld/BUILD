load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:python.bzl", "py_binary", "py_test")

py_binary(
    name = "blockworld",
    srcs = ["blockworld.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("numpy"),
        requirement("rich-click"),
        requirement("openai"),
        ":closed_loop_llm",
        ":environment",
        ":heuristic",
        ":heuristic_llm",
        ":mdp_llm",
        ":mdp_manual",
        ":metrics",
        ":open_loop_llm",
        ":plot",
        "//nlb/util:click_utils",
        "//nlb/util:console_utils",
        "//nlb/util:dataframe",
        "//nlb/util:path_utils",
        "//nlb/util:secrets",
        "//nlb/util:timer",
    ],
)

py_library(
    name = "blockworld_sample_mdp",
    srcs = ["blockworld_sample_mdp.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":environment",
    ],
)

py_library(
    name = "closed_loop_llm",
    srcs = ["closed_loop_llm.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("openai"),
        requirement("openai-agents"),
        ":environment",
        ":metrics",
        "//nlb/util:console_utils",
    ],
)

py_library(
    name = "environment",
    srcs = ["environment.py"],
    visibility = ["//visibility:public"],
    deps = [requirement("numpy")],
)

py_library(
    name = "heuristic",
    srcs = ["heuristic.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":environment",
        ":metrics",
    ],
)

py_library(
    name = "heuristic_llm",
    srcs = ["heuristic_llm.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("openai"),
        requirement("openai-agents"),
        ":environment",
        ":metrics",
        "//nlb/util:console_utils",
    ],
)

py_test(
    name = "heuristic_loading_test",
    srcs = ["heuristic_loading_test.py"],
    data = [":heuristic_llm_sample_policy.txt"],
    deps = [
        ":environment",
        "//nlb/util:console_utils",
    ],
)

py_library(
    name = "mdp",
    srcs = ["mdp.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("numpy"),
        ":environment",
    ],
)

py_library(
    name = "mdp_llm",
    srcs = ["mdp_llm.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("numpy"),
        requirement("openai"),
        requirement("openai-agents"),
        ":environment",
        ":mdp",
        ":metrics",
        "//nlb/util:console_utils",
        "//nlb/util:timeout",
    ],
)

py_library(
    name = "mdp_manual",
    srcs = ["mdp_manual.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":blockworld_sample_mdp",
        ":environment",
        ":mdp",
        ":metrics",
        "//nlb/util:console_utils",
    ],
)

py_library(
    name = "metrics",
    srcs = ["metrics.py"],
    visibility = ["//visibility:public"],
    deps = [],
)

py_library(
    name = "open_loop_llm",
    srcs = ["open_loop_llm.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("openai"),
        requirement("openai-agents"),
        ":environment",
        ":metrics",
        "//nlb/util:console_utils",
    ],
)

py_binary(
    name = "plot",
    srcs = ["plot.py"],
    visibility = ["//visibility:public"],
    data = [
        ":claw.png",
    ],
    deps = [
        requirement("imageio"),
        requirement("matplotlib"),
        requirement("numpy"),
        requirement("pandas"),
        requirement("pillow"),
        requirement("rich-click"),
        ":environment",
        ":metrics",
        "//nlb/util:console_utils",
        "//nlb/util:path_utils",
    ],
)
