load("@rules_cc//cc:defs.bzl", "cc_import")

cc_import(
    name = "libzmq",
    hdrs = glob(["include/*.h"]),
    static_library = "lib/libzmq.a",
    visibility = ["//visibility:public"],
)
