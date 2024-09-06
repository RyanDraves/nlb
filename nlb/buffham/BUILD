load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_test")

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
        "testdata/*.bh",
        "testdata/*.py.golden",
    ]),
    deps = [
        ":engine",
        ":parser",
        ":py_generator",
        "//emb/network/node:dataclass_node",
        # Transitive dependency of our generated code
        "//emb/network/serialize:cbor2_cobs",
    ],
)
