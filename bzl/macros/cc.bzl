load("@rules_cc//cc:defs.bzl", "cc_test", _cc_binary = "cc_binary", _cc_library = "cc_library")
load("//bzl/rules:platform_transition.bzl", "platform_transition")

def cc_binary(name, deps = [], **kwargs):
    _cc_binary(
        name = name,
        deps = deps + select({
            "//bzl/platforms:xtensa": [
                "//toolchains:esp_clang_sys_includes",
            ],
            "//conditions:default": [],
        }),
        **kwargs
    )

def cc_library(name, deps = [], **kwargs):
    _cc_library(
        name = name,
        deps = deps + select({
            "//bzl/platforms:xtensa": [
                "//toolchains:esp_clang_sys_includes",
            ],
            "//conditions:default": [],
        }),
        **kwargs
    )

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
            "@com_google_googletest//:gtest_main",
        ],
    )

    platform_transition(
        name = name + "_platformed",
        dep = name + "_lib",
        platform = "//bzl/platforms:host_unittest",
        visibility = kwargs.get("visibility", ["//visibility:public"]),
        testonly = True,
    )

    cc_test(
        name = name,
        deps = [name + "_platformed"],
        env = kwargs.get("env", {}).update({"UNITTEST": "1"}),
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
            "@com_google_googletest//:gtest_main",
        ],
        env = {"UNITTEST": "1"} | kwargs.get("env", {}),
        **kwargs
    )
