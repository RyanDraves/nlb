load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")

py_library(
    name = "client",
    srcs = ["client.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//nlb/buffham:bh",
    ],
)

py_library(
    name = "host_test_base",
    srcs = ["host_test_base.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":client",
        "//emb/network/transport:tcp",
        "//nlb/buffham:bh",
        requirement("portpicker"),
    ],
)

py_library(
    name = "shell",
    srcs = ["shell.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":client",
        "//emb/network/transport:ble",
        "//emb/network/transport:tcp",
        "//emb/network/transport:usb",
        "//nlb/util:click_utils",
        requirement("rich-click"),
        requirement("IPython"),
    ],
)
