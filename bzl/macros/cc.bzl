"""Wrappers for cross-platform C++ building"""

load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_test")
load("@bazel_skylib//rules:expand_template.bzl", "expand_template")
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")

def _cc_unittest_impl(name, visibility, srcs, deps, env, **kwargs):
    cc_library(
        name = name + "_lib",
        srcs = srcs,
        deps = deps + [
            "@googletest//:gtest_main",
        ],
    )

    cc_test(
        name = name + "_intermediate",
        deps = [name + "_lib"],
        env = {"UNITTEST": "1"} | env,
        # Make sure we don't run this test alongside the transitioned test
        tags = ["manual"],
        **kwargs
    )

    platform_transition_test(
        name = name,
        binary = name + "_intermediate",
        target_platform = "//bzl/platforms:host_unittest",
        visibility = visibility,
    )

def _cc_host_test_impl(name, visibility, srcs, deps, env, **kwargs):
    cc_test(
        name = name,
        srcs = srcs,
        deps = deps + [
            "@googletest//:gtest_main",
        ],
        env = {"UNITTEST": "1"} | env,
        visibility = visibility,
        **kwargs
    )

def _cc_alias_library_impl(name, visibility, lib_select, alias_classname, include_and_classname, **kwargs):
    namespace = native.package_name().split("/")
    begin_namespace = " ".join(["namespace {0} {{".format(part) for part in namespace])
    end_namespace = " ".join(["}" for part in namespace])

    native.alias(
        name = name + "_dep",
        actual = lib_select,
    )

    expand_template(
        name = name + "_include",
        out = name + ".hpp",
        substitutions = {
                            "{alias_classname}": alias_classname,
                            "{begin_namespace}": begin_namespace,
                            "{end_namespace}": end_namespace,
                        } |
                        include_and_classname,
        template = "//bzl/macros:cc_alias.hpp.template",
    )

    cc_library(
        name = name,
        hdrs = [name + "_include"],
        deps = [name + "_dep"],
        visibility = visibility,
        **kwargs
    )

cc_unittest = macro(
    # cc_test still a legacy macro
    # inherit_attrs = cc_test,
    implementation = _cc_unittest_impl,
    doc = "A cc_test that uses an explicit `host_unittest` platform",
    attrs = {
        "srcs": attr.label_list(
            mandatory = True,
            allow_files = True,
            doc = "The source files for the test",
        ),
        "deps": attr.label_list(
            mandatory = True,
            allow_files = False,
            doc = "The dependencies for the test",
        ),
        "env": attr.string_dict(
            doc = "The environment variables for the test",
        ),
    },
)

cc_host_test = macro(
    # cc_test still a legacy macro
    # inherit_attrs = cc_test,
    implementation = _cc_host_test_impl,
    doc = "A cc_test with basic boilerplate setup",
    attrs = {
        "srcs": attr.label_list(
            mandatory = True,
            allow_files = True,
            doc = "The source files for the test",
        ),
        "deps": attr.label_list(
            mandatory = True,
            allow_files = False,
            doc = "The dependencies for the test",
        ),
        "env": attr.string_dict(
            doc = "The environment variables for the test",
        ),
    },
)

cc_alias_library = macro(
    # cc_library still a legacy macro
    # inherit_attrs = cc_library,
    implementation = _cc_alias_library_impl,
    doc = """Create an alias library for a C++ library that remaps a class name

    `include_and_classname` should be structured as:
    ```
    include_and_classname = {
        "{include_path}": "path/to/include.hpp",
        "{dep_classname}": "Classname",
    }
    ```
    This is wrapped in a `select` for the right dependency resolution.

    The generated library can be included as `#include "{name}.hpp"`
    """,
    attrs = {
        "lib_select": attr.label(
            mandatory = True,
            allow_single_file = False,
            doc = "The `select`ed dependency for the alias library",
        ),
        "alias_classname": attr.string(
            mandatory = True,
            doc = "The class name of the alias library",
            # Prevent receiving a `select` object on the input
            configurable = False,
        ),
        "include_and_classname": attr.string_dict(
            mandatory = True,
            doc = "The include file and class name of the alias library",
        ),
    },
)
