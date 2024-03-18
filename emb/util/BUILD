package(default_visibility = ["//visibility:public"])

cc_library(
    name = "cobs",
    hdrs = ["cobs.hpp"],
)

cc_test(
    name = "cobs_test",
    srcs = ["cobs_test.cc"],
    copts = ["-std=c++23"],
    visibility = ["//visibility:public"],
    deps = [
        ":cobs",
        "@com_google_googletest//:gtest_main",
    ],
)
