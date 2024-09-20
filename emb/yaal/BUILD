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
                "@pico-sdk//src/rp2_common/hardware_flash",
            ],
            "//conditions:default": [],
        },
    ),
)
