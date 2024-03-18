# Copied from https://github.com/psigen/bazel-python-cpp-example/blob/281d520ce456f6f41bd1f042401594693a98a5d7/binding/BUILD.bazel
# (including the comment that this was adapted from a Github issue)

# Adapted from: https://github.com/bazelbuild/bazel/issues/1475
cc_binary(
    name = "util.so",
    srcs = ["util.cpp"],
    linkshared = 1,
    linkstatic = 1,
    visibility = ["//visibility:public"],
    deps = [
        "//emb/util:cobs",
        "@pybind11",
        # Haven't figured out how to use Python headers from our
        # 3.12 toolchain, so using the 3.9 headers for now.
        "@python_3_12//:python_headers",
    ],
)

py_library(
    name = "util",
    data = [":util.so"],
    imports = ["."],
    visibility = ["//visibility:public"],
)
