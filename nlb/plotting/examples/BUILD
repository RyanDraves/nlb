load("//bzl/macros:python.bzl", "py_binary")

py_binary(
    name = "colorblind_demo",
    srcs = ["colorblind_demo.py"],
    add_completions = False,
    visibility = ["//visibility:public"],
    deps = [
        "//nlb/plotting:daltonize",
        "//nlb/plotting:palette",
        "@pip//matplotlib",
        "@pip//numpy",
    ],
)

py_binary(
    name = "tol_bright",
    srcs = ["tol_bright.py"],
    add_completions = False,
    visibility = ["//visibility:public"],
    deps = [
        "//nlb/plotting:daltonize",
        "//nlb/plotting:palette",
        "@pip//matplotlib",
        "@pip//numpy",
    ],
)
