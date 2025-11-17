load("@bazel_env.bzl", "bazel_env")
load("@gazelle//:go_tools.bzl", "GO_TOOLS")
load("@multitool//:tools.bzl", MULTITOOL_TOOLS = "TOOLS")

bazel_env(
    name = "bazel_env",
    toolchains = {
        # Go requires Bazel 9.0.0+ (pre-release)
        # "go": "@rules_go//go:toolchain",
        "nodejs": "@nodejs_toolchains//:resolved_toolchain",
        # Isn't happy for some reason
        # "rust": "@rules_rust//rust/toolchain:current_rust_toolchain",
    },
    tools = {
        # Bazel
        "buildifier": "@buildifier_prebuilt//:buildifier",
        "buildozer": "@buildifier_prebuilt//:buildozer",
        # Pico
        "picotool": "@picotool",
        "pioasm": ":pioasm",
        # Go
        "go": "@rules_go//go",
        # NodeJS
        "node": "$(NODE_PATH)",
        "pnpm": "@pnpm",
        # Rust
        "cargo": "@rules_rust//tools/upstream_wrapper:cargo",
        "rustfmt": "@rules_rust//tools/upstream_wrapper:rustfmt",
    } | MULTITOOL_TOOLS | GO_TOOLS,
)
