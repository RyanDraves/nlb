load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip//:requirements.bzl", "requirement")
load("//bzl/macros:buffham.bzl", "buffham", "buffham_py_write", "buffham_template")
load("//bzl/macros:python.bzl", "py_binary", "py_test")

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
        ":cpp_generator",
        ":parser",
        ":py_generator",
        ":template_generator",
        "//nlb/util:click_utils",
        requirement("rich-click"),
    ],
)

py_library(
    name = "cpp_generator",
    srcs = ["cpp_generator.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":parser",
    ],
)

py_test(
    name = "cpp_generator_test",
    srcs = ["cpp_generator_test.py"],
    data = [
        "testdata/sample_bh.cc",
        "testdata/sample_bh.cc.golden",
        "testdata/sample_bh.hpp",
        "testdata/sample_bh.hpp.golden",
    ],
    env = {
        "TEST_HPP": "testdata/sample_bh.hpp",
        "TEST_CC": "testdata/sample_bh.cc",
    },
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
        ":testdata/other_bh_py",
        ":bh",
        # Transitive dependency of our generated code
        "//emb/network/serialize:bh_cobs",
    ],
)

py_library(
    name = "template_generator",
    srcs = ["template_generator.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":parser",
    ],
)

py_test(
    name = "template_generator_test",
    srcs = ["template_generator_test.py"],
    data = [
        "testdata/sample.md.golden",
        "testdata/sample.template.md",
        "testdata/sample_template.md",
    ],
    env = {
        "TEST_FILE": "testdata/sample_template.md",
    },
)

buffham(
    name = "testdata/other_bh",
    src = "testdata/other.bh",
    cc = True,
    py = True,
    visibility = ["__pkg__"],
    tags = ["testdata"],
)

buffham(
    name = "testdata/sample_bh",
    src = "testdata/sample.bh",
    cc = True,
    py = True,
    visibility = ["__pkg__"],
    deps = [":testdata/other_bh"],
    tags = ["testdata"],
)

buffham_py_write(
    name = "testdata/sample_bh_py_write",
)

buffham_template(
    name = "testdata/sample_template",
    bh = ":testdata/sample_bh",
    bh_deps = [":testdata/other_bh"],
    out_file = "testdata/sample_template.md",
    template = "testdata/sample.template.md",
)
