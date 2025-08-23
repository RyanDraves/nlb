load(":workspace_tool.bzl", "workspace_tool")
load("@rules_java//java:java_binary.bzl", "java_binary")

workspace_tool(
    name = "buildifier",
    tool = "@buildifier_prebuilt//:buildifier",
)

workspace_tool(
    name = "buildozer",
    tool = "@buildifier_prebuilt//:buildozer",
)

workspace_tool(
    name = "picotool",
    tool = "@picotool",
)

java_binary(
   name = "copybara",
   main_class = "com.google.copybara.Main",
   runtime_deps = ["@copybara//jar"],
)

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
