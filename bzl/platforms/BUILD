package(default_visibility = ["//visibility:public"])

constraint_setting(
    name = "host_type",
)

constraint_value(
    name = "unittest",
    constraint_setting = ":host_type",
)

platform(
    name = "host_unittest",
    constraint_values = [
        ":unittest",
    ],
    parents = ["@platforms//host"],
)

constraint_value(
    name = "xtensa",
    constraint_setting = "@platforms//cpu",
)

platform(
    name = "esp32",
    constraint_values = [
        "@platforms//os:none",
        ":xtensa",
    ],
)
