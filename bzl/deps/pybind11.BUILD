# Copied from https://github.com/psigen/bazel-python-cpp-example/blob/281d520ce456f6f41bd1f042401594693a98a5d7/pybind11.BUILD
# (including the comment that this was adapted from TensorFlow)

# Adapted from TensorFlow.
package(default_visibility = ["//visibility:public"])

cc_library(
    name = "pybind11",
    hdrs = glob(
        include = [
            "include/pybind11/*.h",
            "include/pybind11/detail/*.h",
        ],
        exclude = [
            "include/pybind11/common.h",
            "include/pybind11/eigen.h",
        ],
    ),
    copts = [
        "-fexceptions",
        "-Wno-undefined-inline",
        "-Wno-pragma-once-outside-header",
    ],
    includes = ["include"],
)
