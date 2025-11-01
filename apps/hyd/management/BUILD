load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//bzl/macros:python.bzl", "py_binary")

py_library(
    name = "__init__",
    srcs = ["__init__.py"],
    visibility = ["//:__subpackages__"],
)

py_library(
    name = "client",
    srcs = ["client.py"],
    visibility = ["//:__subpackages__"],
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
    visibility = ["//:__subpackages__"],
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
    visibility = ["//:__subpackages__"],
    deps = [
        ":schema",
        "@pip//alembic",
        "@pip//sqlalchemy",
    ],
)

py_library(
    name = "schema",
    srcs = ["schema.py"],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//sqlalchemy"],
)
