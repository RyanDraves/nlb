package(default_visibility = ["//visibility:public"])

constraint_setting(
    name = "c_family",
)

constraint_value(
    name = "23",
    constraint_setting = ":c_family",
)

constraint_value(
    name = "c",
    constraint_setting = ":c_family",
)

platform(
    name = "pico",
    constraint_values = [
        "@platforms//os:none",
        "@platforms//cpu:armv6-m",
        ":23",
    ],
)

platform(
    name = "pico_c",
    constraint_values = [
        "@platforms//os:none",
        "@platforms//cpu:armv6-m",
        ":c",
    ],
)
