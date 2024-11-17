load("//bzl/macros:pico.bzl", "pio_cc_library")

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
            "//conditions:default": [
            ],
        },
    ) + ["//emb/project/bootloader:bootloader_bh_cc"],
)

cc_library(
    name = "gpio",
    srcs = select(
        {
            "@platforms//cpu:armv6-m": ["pico/gpio.cc"],
            # Same as host, for now
            "//bzl/platforms:unittest": ["host/gpio.cc"],
            "//conditions:default": ["host/gpio.cc"],
        },
    ),
    hdrs = ["gpio.hpp"],
    visibility = ["//visibility:public"],
    deps = select(
        {
            "@platforms//cpu:armv6-m": [
                "@pico-sdk//src/rp2_common/hardware_gpio",
                "@pico-sdk//src/rp2_common/pico_stdlib",
            ],
            "//conditions:default": [
            ],
        },
    ),
)

cc_library(
    name = "host_gpio",
    hdrs = ["host/gpio.hpp"],
    visibility = ["//visibility:public"],
    deps = [":gpio"],
)

cc_library(
    name = "pio",
    hdrs = ["pio.hpp"],
    visibility = ["//visibility:public"],
)

cc_library(
    name = "timer",
    srcs = select(
        {
            "@platforms//cpu:armv6-m": ["pico/timer.cc"],
            # Same as host, for now
            "//bzl/platforms:unittest": ["host/timer.cc"],
            "//conditions:default": ["host/timer.cc"],
        },
    ),
    hdrs = ["timer.hpp"] + select(
        {
            "@platforms//cpu:armv6-m": [],
            # Same as host, for now
            "//bzl/platforms:unittest": ["host/timer.hpp"],
            "//conditions:default": ["host/timer.hpp"],
        },
    ),
    visibility = ["//visibility:public"],
    deps = select(
        {
            "@platforms//cpu:armv6-m": [
                "@pico-sdk//src/rp2_common/hardware_timer",
                "@pico-sdk//src/rp2_common/pico_stdlib",
            ],
            "//conditions:default": [
            ],
        },
    ),
)

cc_library(
    name = "watchdog",
    srcs = select(
        {
            "@platforms//cpu:armv6-m": ["pico/watchdog.cc"],
            # Same as host, for now
            "//bzl/platforms:unittest": ["host/watchdog.cc"],
            "//conditions:default": ["host/watchdog.cc"],
        },
    ),
    hdrs = ["watchdog.hpp"],
    visibility = ["//visibility:public"],
    deps = select(
        {
            "@platforms//cpu:armv6-m": [
                "@pico-sdk//src/rp2_common/hardware_watchdog",
            ],
            "//conditions:default": [],
        },
    ),
)

#
# Library of PIO programs
#
pio_cc_library(
    name = "pio_blink",
    srcs = select(
        {
            "@platforms//cpu:armv6-m": ["pico/pio/blink.cc"],
            # Same as host, for now
            "//bzl/platforms:unittest": ["host/pio/blink.cc"],
            "//conditions:default": ["host/pio/blink.cc"],
        },
    ),
    hdrs = ["pio/blink.hpp"],
    pio = "pico/pio/blink.pio",
    visibility = ["//visibility:public"],
    deps = [":pio"] + select(
        {
            "@platforms//cpu:armv6-m": [
                "@pico-sdk//src/rp2_common/hardware_clocks",
                "@pico-sdk//src/rp2_common/hardware_pio",
            ],
            "//conditions:default": [],
        },
    ),
)
