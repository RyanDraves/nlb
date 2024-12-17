load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_test")
load("@bazel_skylib//rules:expand_template.bzl", "expand_template")
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")

def cc_unittest(name, srcs, deps, **kwargs):
    """A cc_test that uses an explicit `host_unittest` platform.

    Args:
        name: The name of the test.
        srcs: The source files for the test.
        deps: The dependencies for the test.
        **kwargs: Additional arguments to pass to cc_test.
    """
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
        env = kwargs.get("env", {}).update({"UNITTEST": "1"}),
        # Make sure we don't run this test alongside the transitioned test
        tags = ["manual"],
    )

    platform_transition_test(
        name = name,
        binary = name + "_intermediate",
        target_platform = "//bzl/platforms:host_unittest",
        **kwargs
    )

def cc_host_test(name, srcs, deps, **kwargs):
    """A cc_test with basic boilerplate setup

    Args:
        name: The name of the test.
        srcs: The source files for the test.
        deps: The dependencies for the test.
        **kwargs: Additional arguments to pass to cc_test.
    """
    cc_test(
        name = name,
        srcs = srcs,
        deps = deps + [
            "@googletest//:gtest_main",
        ],
        env = {"UNITTEST": "1"} | kwargs.get("env", {}),
        **kwargs
    )

def cc_alias_library(name, lib_select, alias_classname, include_and_classname, **kwargs):
    """Create an alias library for a C++ library that remaps a class name

    `include_and_classname` should be structured as:
    ```
    include_and_classname = {
        "{include_path}": "path/to/include.hpp",
        "{dep_classname}": "Classname",
    }
    ```
    This is wrapped in a `select` for the right dependency resolution

    Args:
        name: The name of the alias library
        lib_select: The `select`ed dependency for the alias library
        alias_classname: The class name of the alias library
        include_and_classname: The include file and class name of the alias library
        **kwargs: Additional arguments to pass to `cc_library`
    """
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
        **kwargs
    )
