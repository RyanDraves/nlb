load("@aspect_rules_py//py:defs.bzl", "py_library")

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
        "@pip//portpicker",
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
        "//emb/network/transport:transporter",
        "//emb/network/transport:usb",
        "//nlb/buffham:bh",
        "//nlb/util:click_utils",
        "@pip//ipython",
        "@pip//rich_click",
    ],
)
