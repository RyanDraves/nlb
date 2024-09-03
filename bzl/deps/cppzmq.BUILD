load("@rules_foreign_cc//foreign_cc:defs.bzl", "cmake")

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "sources",
    srcs = glob([
        "*.hpp",
        "libzmq-pkg-config/*",
        "cmake/*",
    ]) + [
        "CMakeLists.txt",
        "cppzmq.pc.in",
        "cppzmqConfig.cmake.in",
        "version.sh",
    ],
    visibility = ["//visibility:public"],
)

cmake(
    name = "cppzmq",
    generate_args = [
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCPPZMQ_BUILD_TESTS=OFF",
    ],
    lib_source = ":sources",
    out_headers_only = True,
    visibility = ["//visibility:public"],
    deps = [
        "@libzmq//:ZeroMQ",
    ],
)
