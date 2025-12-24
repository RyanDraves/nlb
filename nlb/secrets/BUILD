load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_test")

py_library(
    name = "secrets",
    srcs = ["secrets.py"],
    visibility = ["//visibility:public"],
    deps = [":setec_client"],
)

py_library(
    name = "setec_client",
    srcs = ["setec_client.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//marshmallow_dataclass",
        "@pip//requests",
    ],
)

py_test(
    name = "setec_client_test",
    srcs = ["setec_client_test.py"],
    deps = [
        ":setec_client",
        "@pip//pytest",
        "@pip//responses",
    ],
)
