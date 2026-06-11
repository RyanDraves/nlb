load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_binary", "py_test")

py_library(
    name = "wav2cc_lib",
    srcs = ["wav2cc.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//numpy",
        "@pip//rich_click",
        "@pip//scipy",
    ],
)

py_binary(
    name = "wav2cc",
    srcs = ["wav2cc.py"],
    main = "wav2cc.py",
    visibility = ["//visibility:public"],
    deps = [
        "@pip//numpy",
        "@pip//rich_click",
        "@pip//scipy",
    ],
)

py_test(
    name = "wav2cc_test",
    srcs = ["wav2cc_test.py"],
    deps = [
        "//nlb/wav:wav2cc_lib",
        "@pip//numpy",
        "@pip//scipy",
    ],
)
