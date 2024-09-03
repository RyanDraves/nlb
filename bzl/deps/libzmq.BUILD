load("@rules_foreign_cc//foreign_cc:defs.bzl", "cmake")

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "sources",
    srcs = glob([
        "src/**/*",
        "include/**/*",
        "builds/cmake/**/*",
        "external/**/*",
    ]) + [
        "AUTHORS",
        "CMakeLists.txt",
        "LICENSE",
        "NEWS",
        "version.sh",
    ],
    visibility = ["//visibility:public"],
)

cmake(
    # Name carefully chosen to match the CMake package name;
    # see https://github.com/bazelbuild/rules_foreign_cc/issues/1195#issuecomment-2081572645
    name = "ZeroMQ",
    generate_args = [
        "-DCMAKE_BUILD_TYPE=Release",
        "-DWITH_PERF_TOOL=OFF",
        "-DZMQ_BUILD_TESTS=OFF",
    ],
    lib_source = ":sources",
    out_static_libs = ["libzmq.a"],
    visibility = ["//visibility:public"],
)
