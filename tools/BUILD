load("@bazel_env.bzl", "bazel_env")
load(":workspace_tool.bzl", "workspace_tool")

# workspace_tool(
#     name = "buildifier",
#     tool = "@buildifier_prebuilt//:buildifier",
# )

# workspace_tool(
#     name = "buildozer",
#     tool = "@buildifier_prebuilt//:buildozer",
# )

# workspace_tool(
#     name = "picotool",
#     tool = "@picotool",
# )

alias(
    name = "pioasm",
    actual = select(
        {
            "@platforms//cpu:x86_64": "@pioasm-linux-x86//:pioasm",
            "@platforms//cpu:aarch64": "@pioasm-linux-arm//:pioasm",
        },
    ),
    visibility = ["//visibility:public"],
)

bazel_env(
    name = "bazel_env",
    toolchains = {
        "jdk": "@rules_java//toolchains:current_host_java_runtime",
    },
    tools = {
        # Tools can be specified as labels.
        "buildifier": "@buildifier_prebuilt//:buildifier",
        "buildozer": "@buildifier_prebuilt//:buildozer",
        "picotool": "@picotool",
    },
)
