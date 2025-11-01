load("@bazel_lib//lib:write_source_files.bzl", "write_source_files")
load("@buildifier_prebuilt//:rules.bzl", "buildifier")
load("@gazelle//:def.bzl", "gazelle", "gazelle_binary")
load("@hedron_compile_commands//:refresh_compile_commands.bzl", "refresh_compile_commands")
load("@npm//:defs.bzl", "npm_link_all_packages")
load("@pip//:requirements.bzl", "all_whl_requirements")
load("@rules_python_gazelle_plugin//manifest:defs.bzl", "gazelle_python_manifest")
load("@rules_python_gazelle_plugin//modules_mapping:def.bzl", "modules_mapping")
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

gazelle_binary(
    name = "gazelle_multilang",
    languages = [
        #182 use https://github.com/bazel-starters/py/blob/main/BUILD#L26
        "@rules_python_gazelle_plugin//python",
    ],
)

gazelle(
    name = "gazelle",
    gazelle = ":gazelle_multilang",
)

# gazelle:build_file_name BUILD

# Customize mappings for Python rules
# gazelle:map_kind py_binary py_binary //bzl/macros:python.bzl
# gazelle:map_kind py_library py_library @aspect_rules_py//py:defs.bzl
# gazelle:map_kind py_test py_test //bzl/macros:python.bzl
#
# Don't walk into generated folders
# gazelle:exclude venv/
# gazelle:exclude external/
# gazelle:exclude node_modules/
#
# Fetches metadata for python packages we depend on.
modules_mapping(
    name = "modules_map",
    include_stub_packages = False,
    wheels = all_whl_requirements,
)

# Provide a mapping from an import to the installed package that provides it.
# Needed to generate BUILD files for .py files.
# This macro produces two targets:
# - //:gazelle_python_manifest.update can be used with `bazel run`
#   to recalculate the manifest
# - //:gazelle_python_manifest.test is a test target ensuring that
#   the manifest doesn't need to be updated
gazelle_python_manifest(
    name = "gazelle_python_manifest",
    modules_mapping = ":modules_map",
    # Name of `pip.parse` rule in `MODULE.bazel`
    pip_repository_name = "pip",
    requirements = "//:requirements_lock.txt",
)

# More Gazelle Python directives
#
# gazelle:python_test_file_pattern *_test.py
# gazelle:python_generation_mode file
#
# gazelle:python_ignore_files services/authentik/invitation_group_add.py
#
# Generated libraries
# gazelle:resolve py emb.network.frame.cobs //emb/network/frame:cobs_py
#
# Buffham files
# gazelle:resolve_regexp py emb.network.serialize.testdata.test_bh //emb/network/serialize:testdata/test_bh_py
# gazelle:resolve_regexp py emb.network.transport.nus_bh //emb/network/transport:nus_bh_py
# gazelle:resolve_regexp py emb.project.base.base_bh //emb/project/base:base_bh_py
# gazelle:resolve_regexp py emb.project.bootloader.bootloader_bh //emb/project/bootloader:bootloader_bh_py
# gazelle:resolve_regexp py emb.project.robo24.robo24_bh //emb/project/robo24:robo24_bh_py
# gazelle:resolve_regexp py nlb.buffham.testdata.sample_bh //nlb/buffham:testdata/sample_bh_py
# gazelle:resolve_regexp py nlb.buffham.testdata.other_bh //nlb/buffham:testdata/other_bh_py
