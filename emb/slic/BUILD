load("//bzl/macros:unittest.bzl", "cc_unittest")

cc_library(
    name = "hc_sr04",
    srcs = ["hc_sr04.cc"],
    hdrs = ["hc_sr04.hpp"],
    implementation_deps = [
        "//emb/yaal:timer",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "//emb/yaal:gpio",
    ],
)

cc_unittest(
    name = "hc_sr04_test",
    srcs = ["hc_sr04_test.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":hc_sr04",
    ],
)
