load("@aspect_bazel_lib//lib:write_source_files.bzl", "write_source_files")
load("@buildifier_prebuilt//:rules.bzl", "buildifier")
load("@hedron_compile_commands//:refresh_compile_commands.bzl", "refresh_compile_commands")
load("@npm//:defs.bzl", "npm_link_all_packages")
load("@rules_uv//uv:pip.bzl", "pip_compile")
load("@rules_uv//uv:venv.bzl", "create_venv")

package(default_visibility = ["//:__subpackages__"])

# Create the root of the "virtual store" of npm dependencies under bazel-out
npm_link_all_packages(name = "node_modules")

buildifier(
    name = "buildifier.check",
    diff_command = "diff -u",
    lint_mode = "warn",
    mode = "diff",
)

buildifier(
    name = "buildifier.fix",
    lint_mode = "fix",
    mode = "fix",
)

pip_compile(
    name = "requirements",
    requirements_in = "//:requirements.txt",
    requirements_txt = "//:requirements_lock.txt",
)

create_venv(
    name = "venv",
    requirements_txt = "//:requirements_lock.txt",
)

# Usage:
#  - Build all targets with flags
#    - bazel build --config pico //emb/...
#  - bazel run //:refresh_compile_commands
refresh_compile_commands(
    name = "refresh_compile_commands",

    # Specify the targets of interest.
    # For example, specify a dict of targets and any flags required to build.
    targets = {
        "//emb/...": "",
    },
)

write_source_files(
    name = "generate_bh",
    additional_update_targets = [
        "//emb/network/serialize:testdata/test_bh_py_write",
        "//emb/network/transport:nus_bh_py_write",
        "//emb/project/base:base_bh_py_write",
        "//emb/project/bootloader:bootloader_bh_py_write",
        "//emb/project/robo24:robo24_bh_py_write",
        "//nlb/buffham:testdata/sample_bh_py_write",
    ],
)
