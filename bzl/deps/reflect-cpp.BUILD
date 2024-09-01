load("@rules_foreign_cc//foreign_cc:defs.bzl", "cmake")

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "sources",
    srcs = glob([
        "src/**/*",
        "include/**/*",
    ]) + [
        "CMakeLists.txt",
        "reflectcpp-config.cmake.in",
    ],
    visibility = ["//visibility:public"],
)

cmake(
    name = "refl",
    generate_args = [
        "-DCMAKE_BUILD_TYPE=Release",
        "-DREFLECTCPP_CBOR=True",
        "-DREFLECTCPP_BUILD_SHARED=False",
    ],
    lib_source = ":sources",
    out_static_libs = ["libreflectcpp.a"],
    visibility = ["//visibility:public"],
    deps = [
        "@tinycbor//:cbor",
    ],
)
