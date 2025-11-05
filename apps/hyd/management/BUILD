load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_binary")

py_library(
    name = "__init__",
    srcs = ["__init__.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "client",
    srcs = ["client.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":schema",
        "@pip//python_dotenv",
        "@pip//sqlalchemy",
    ],
)

py_binary(
    name = "db_manager",
    srcs = ["db_manager.py"],
    add_completions = False,
    visibility = ["//visibility:public"],
    deps = [
        ":client",
        ":schema",
        "//nlb/util:click_utils",
        "//nlb/util:path_utils",
        "@pip//alembic",
        "@pip//rich_click",
    ],
)

py_library(
    name = "env",
    srcs = ["env.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":schema",
        "@pip//alembic",
        "@pip//sqlalchemy",
    ],
)

py_library(
    name = "schema",
    srcs = ["schema.py"],
    visibility = ["//visibility:public"],
    deps = ["@pip//sqlalchemy"],
)
