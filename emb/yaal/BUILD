cc_library(
    name = "flash",
    srcs = select(
        {
            "@platforms//cpu:armv6-m": ["pico/flash.cc"],
            # Same as host, for now
            "//bzl/platforms:unittest": ["host/flash.cc"],
            "//conditions:default": ["host/flash.cc"],
        },
    ),
    hdrs = ["flash.hpp"],
    visibility = ["//visibility:public"],
    deps = select(
        {
            "@platforms//cpu:armv6-m": [
                "//bzl/deps:pico_stdlib_c",
            ],
            "//conditions:default": [],
        },
    ) + ["//emb/project/base:base_bh_cc"],
)
