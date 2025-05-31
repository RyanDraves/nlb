"""Macro for creating a target that runs a tool from the workspace.

Adapted from https://dev.to/bazel/bazel-can-write-to-the-source-folder-b9b
"""

load("@bazel_skylib//rules:write_file.bzl", "write_file")
load("@rules_shell//shell:sh_binary.bzl", "sh_binary")

def workspace_tool(name, tool):
    write_file(
        name = name + "_file",
        out = name + ".sh",
        content = [
            "#!/bin/bash",
            "EXEC_ROOT=$(pwd)",
            'cd "$BUILD_WORKSPACE_DIRECTORY"',
            'exec "$EXEC_ROOT/$1" "${@:2}"',
        ],
    )

    sh_binary(
        name = name,
        srcs = [name + ".sh"],
        data = [tool],
        args = ["$(location {tool})".format(tool = tool)],
    )
