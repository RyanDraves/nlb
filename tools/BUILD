load(":workspace_tool.bzl", "workspace_tool")

workspace_tool(
    name = "buildifier",
    tool = "@buildifier_prebuilt//:buildifier",
)

workspace_tool(
    name = "picotool",
    tool = "@picotool",
)

alias(
    name = "pioasm",
    actual = select(
        {
            "@platforms//cpu:x86_64": "@pioasm-linux-x86//:pioasm",
            "@platforms//cpu:aarch64": "@pioasm-linux-arm//:pioasm",
        },
    ),
)
