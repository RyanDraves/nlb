workspace(name = "nlb")

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Pico

http_archive(
    name = "rules_pico",
    integrity = "sha256-eYlQxBLVx4ZKuAU0ptpjc7X13BnYGHIWA76bymUVVLA=",
    strip_prefix = "rules_pico-hermetic-toolchain",
    url = "https://github.com/RyanDraves/rules_pico/archive/refs/heads/hermetic-toolchain.zip",
)

load("@rules_pico//pico:repositories.bzl", "rules_pico_dependencies")

rules_pico_dependencies()

http_archive(
    name = "pico-examples",
    build_file = "@rules_pico//pico:BUILD.pico-examples",
    sha256 = "a07789d702f8e6034c42e04a3f9dda7ada4ae7c8e8d320c6be6675090c007861",
    strip_prefix = "pico-examples-sdk-1.4.0",
    urls = [
        "https://github.com/raspberrypi/pico-examples/archive/refs/tags/sdk-1.4.0.tar.gz",
    ],
)

# Arm toolchain

git_repository(
    name = "arm_none_eabi",
    # commit = "98a38734b7b8f0781a1297cd9173dadd2e215fc8",
    # remote = "https://github.com/hexdae/bazel-arm-none-eabi",
    # https://github.com/hexdae/bazel-arm-none-eabi/pull/31
    commit = "47c74efa1130af28654c281fd4984ced1850022b",
    remote = "https://github.com/RyanDraves/bazel-arm-none-eabi",
)

load("@arm_none_eabi//:deps.bzl", "arm_none_eabi_deps")

arm_none_eabi_deps(version = "13.2.1")

# py_venv export

git_repository(
    name = "rules_pyvenv",
    commit = "0b03b0d1f5562223d1170c511e548dc0961f0c5f",
    remote = "https://github.com/cedarai/rules_pyvenv",
)

#
# Begin nanopb
#
# Nanopb stuff / protobuf just isn't compatible with Python 3.12. Uncommenting
# python_register_toolchains will set our interpreter to 3.9, so leave this
# commented out.
#

# # git_repository(
# #     name = "com_google_protobuf",
# #     remote = "https://github.com/protocolbuffers/protobuf.git",
# #     commit = "a9b006bddd52e289029f16aa77b77e8e0033d9ee",
# # )

# # git_repository(
# #     name = "com_github_nanopb_nanopb",
# #     commit = "6cfe48d6f1593f8fa5c0f90437f5e6522587745e",
# #     remote = "https://github.com/nanopb/nanopb.git",
# # )
# local_repository(
#     name = "com_github_nanopb_nanopb",
#     path = "../nanopb",
# )

# load("@com_github_nanopb_nanopb//extra/bazel:nanopb_deps.bzl", "nanopb_deps")

# nanopb_deps()

# load("@rules_python//python:repositories.bzl", "py_repositories")

# py_repositories()
# # http_archive(
# #     name = "rules_python",
# #     sha256 = "5fa3c738d33acca3b97622a13a741129f67ef43f5fdfcec63b29374cc0574c29",
# #     strip_prefix = "rules_python-0.9.0",
# #     url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.9.0.tar.gz",
# # )

# load("@com_github_nanopb_nanopb//extra/bazel:python_deps.bzl", "nanopb_python_deps")
# # load("@python_versions//:defs.bzl", "interpreter")

# # load("@python_3_12//:defs.bzl", "interpreter")

# http_archive(
#     name = "rules_python_nanopb",
#     sha256 = "5fa3c738d33acca3b97622a13a741129f67ef43f5fdfcec63b29374cc0574c29",
#     strip_prefix = "rules_python-0.9.0",
#     url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.9.0.tar.gz",
# )

# load("@rules_python_nanopb//python:repositories.bzl", "python_register_toolchains")

# python_register_toolchains(
#     name = "python3_9",
#     python_version = "3.9",
#     register_toolchains = True,
# )

# load("@python3_9//:defs.bzl", "interpreter")

# nanopb_python_deps(interpreter)

# load("@com_github_nanopb_nanopb//extra/bazel:nanopb_workspace.bzl", "nanopb_workspace")

# nanopb_workspace()

#
# End nanopb
#

# Google Test
git_repository(
    name = "com_google_googletest",
    commit = "f8d7d77c06936315286eb55f8de22cd23c188571",
    remote = "https://github.com/google/googletest.git",
)

# Pybind11
http_archive(
    name = "pybind11",
    build_file = "//bzl/deps:pybind11.BUILD",
    integrity = "sha256-1HWXjaDNwtQ7c/MJEHhnWdWTqdjuBbG2hG0esWxtLgw=",
    strip_prefix = "pybind11-2.11.1",
    urls = [
        "https://github.com/pybind/pybind11/archive/v2.11.1.tar.gz",
    ],
)

#
# Begin flatbuffers
#
# Flatbuffers does not declare dev dependencies separately, so it has a rather annoying
# set of node things that we need to set up ourself to mirror its behavior.
#

http_archive(
    name = "com_github_google_flatbuffers",
    integrity = "sha256-wEgonACiSSu+F7V2KG7to82atpqJazs6G/adO+No1tU=",
    strip_prefix = "flatbuffers-24.3.7",
    url = "https://github.com/google/flatbuffers/archive/v24.3.7.zip",
)

http_archive(
    name = "aspect_rules_js",
    sha256 = "76a04ef2120ee00231d85d1ff012ede23963733339ad8db81f590791a031f643",
    strip_prefix = "rules_js-1.34.1",
    url = "https://github.com/aspect-build/rules_js/releases/download/v1.34.1/rules_js-v1.34.1.tar.gz",
)

load("@aspect_rules_js//js:repositories.bzl", "rules_js_dependencies")

rules_js_dependencies()

load("@aspect_rules_js//npm:npm_import.bzl", "npm_translate_lock", "pnpm_repository")

pnpm_repository(name = "pnpm")

http_archive(
    name = "aspect_rules_ts",
    sha256 = "4c3f34fff9f96ffc9c26635d8235a32a23a6797324486c7d23c1dfa477e8b451",
    strip_prefix = "rules_ts-1.4.5",
    url = "https://github.com/aspect-build/rules_ts/releases/download/v1.4.5/rules_ts-v1.4.5.tar.gz",
)

load("@aspect_rules_ts//ts:repositories.bzl", "rules_ts_dependencies")

rules_ts_dependencies(
    # Since rules_ts doesn't always have the newest integrity hashes, we
    # compute it manually here.
    #   $ curl --silent https://registry.npmjs.org/typescript/5.3.3 | jq ._integrity
    ts_integrity = "sha512-pXWcraxM0uxAS+tN0AG/BF2TyqmHO014Z070UsJ+pFvYuRSq8KH8DmWpnbXe0pEPDHXZV3FcAbJkijJ5oNEnWw==",
    ts_version_from = "@com_github_google_flatbuffers//:package.json",
)

load("@rules_nodejs//nodejs:repositories.bzl", "DEFAULT_NODE_VERSION", "nodejs_register_toolchains")

nodejs_register_toolchains(
    name = "nodejs",
    node_version = DEFAULT_NODE_VERSION,
)

npm_translate_lock(
    name = "npm",
    npmrc = "@com_github_google_flatbuffers//:.npmrc",
    pnpm_lock = "//:pnpm-lock.yaml",
    # Set this to True when the lock file needs to be updated, commit the
    # changes, then set to False again.
    update_pnpm_lock = False,
    verify_node_modules_ignored = "//:.bazelignore",
)

#
# End flatbuffers
#
