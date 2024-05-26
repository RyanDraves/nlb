load("//bzl/rules:platform_transition.bzl", "platform_transition")

package(default_visibility = ["//visibility:public"])

# Build the pico SDK with gcc; it seems to have incompatibilities with g++
platform_transition(
    name = "pico_stdlib_c",
    dep = "@rules_pico//pico:pico_stdlib",
    platform = "//bzl/platforms:pico_c",
    visibility = ["//:__subpackages__"],
)
