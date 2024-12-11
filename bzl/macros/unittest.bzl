load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_test")
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
