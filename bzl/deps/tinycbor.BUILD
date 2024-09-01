load("@rules_foreign_cc//foreign_cc:defs.bzl", "make")

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "sources",
    srcs = glob([
        "src/**/*",
        "tools/**/*",
    ]) + [
        "Makefile",
        "Makefile.configure",
        "VERSION",
        "tinycbor.pc.in",
    ],
    visibility = ["//visibility:public"],
)

make(
    # Name carefully chosen to match the CMake package name;
    # see https://github.com/bazelbuild/rules_foreign_cc/issues/1195#issuecomment-2081572645
    name = "cbor",
    # Use the undocumented `INSTALLDIR` variable to set the install prefix.
    args = ["prefix=$$INSTALLDIR"],
    lib_source = ":sources",
    out_include_dir = "include/tinycbor",
    out_static_libs = ["libtinycbor.a"],
    targets = [
        "",
        "install",
    ],
    visibility = ["//visibility:public"],
)
