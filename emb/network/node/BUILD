load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:cc.bzl", "cc_library")

py_library(
    name = "dataclass_node",
    srcs = ["dataclass_node.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//emb/network/node",
        "//emb/network/serialize:serializer",
        "//emb/network/transport:transporter",
        "//nlb/util:dataclass",
    ],
)

py_library(
    name = "node",
    srcs = ["node.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//emb/network/serialize:serializer",
        "//emb/network/transport:transporter",
    ],
)

cc_library(
    name = "node_cc",
    hdrs = ["node.hpp"],
    visibility = ["//visibility:public"],
    deps = [
        "//emb/network/serialize:serializer_cc",
        "//emb/network/transport:transporter_cc",
    ],
)
