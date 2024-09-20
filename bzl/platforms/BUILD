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

constraint_setting(
    name = "host_type",
)

constraint_value(
    name = "unittest",
    constraint_setting = ":host_type",
)

platform(
    name = "pico",
    constraint_values = [
        # "@platforms//os:none",
        # "@platforms//cpu:armv6-m",
        ":23",
    ],
    parents = ["@pico-sdk//bazel/platform:rp2040"],
)

platform(
    name = "pico_c",
    constraint_values = [
        "@platforms//os:none",
        "@platforms//cpu:armv6-m",
        ":c",
    ],
)

platform(
    name = "host_unittest",
    constraint_values = [
        ":unittest",
    ],
    parents = ["@platforms//host"],
)
