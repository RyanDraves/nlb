load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:python.bzl", "py_test")

py_library(
    name = "bh",
    srcs = ["bh.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//emb/network/node",
        "//emb/network/transport:transporter",
        "//nlb/util:dataclass",
    ],
)

py_binary(
    name = "buffham",
    srcs = ["buffham.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":parser",
        ":py_generator",
        "//nlb/util:click_utils",
        requirement("rich-click"),
    ],
)

py_library(
    name = "engine",
    srcs = ["engine.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":parser",
        "//nlb/util:dataclass",
    ],
)

py_test(
    name = "engine_test",
    srcs = ["engine_test.py"],
    deps = [
        ":engine",
    ],
)

py_library(
    name = "parser",
    srcs = ["parser.py"],
    visibility = ["//visibility:public"],
    deps = [
    ],
)

py_test(
    name = "parser_test",
    srcs = ["parser_test.py"],
    data = glob(["testdata/*.bh"]),
    deps = [
        ":parser",
    ],
)

py_library(
    name = "py_generator",
    srcs = ["py_generator.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":parser",
    ],
)

py_test(
    name = "py_generator_test",
    srcs = ["py_generator_test.py"],
    data = glob([
        "testdata/*",
    ]),
    deps = [
        ":engine",
        ":parser",
        ":py_generator",
        ":bh",
        # Transitive dependency of our generated code
        "//emb/network/serialize:bh_cobs",
    ],
)
