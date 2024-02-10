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
    commit = "98a38734b7b8f0781a1297cd9173dadd2e215fc8",
    remote = "https://github.com/hexdae/bazel-arm-none-eabi",
    # commit = "6c906b5691aa1b0ddc21094b606b3f6080f6e477",
    # remote = "https://github.com/RyanDraves/bazel-arm-none-eabi",
)

load("@arm_none_eabi//:deps.bzl", "arm_none_eabi_deps")

arm_none_eabi_deps(version = "13.2.1")

# py_venv export

git_repository(
    name = "rules_pyvenv",
    commit = "0b03b0d1f5562223d1170c511e548dc0961f0c5f",
    remote = "https://github.com/cedarai/rules_pyvenv",
)

# nanopb

# git_repository(
#     name = "com_google_protobuf",
#     remote = "https://github.com/protocolbuffers/protobuf.git",
#     commit = "a9b006bddd52e289029f16aa77b77e8e0033d9ee",
# )

# git_repository(
#     name = "com_github_nanopb_nanopb",
#     commit = "6cfe48d6f1593f8fa5c0f90437f5e6522587745e",
#     remote = "https://github.com/nanopb/nanopb.git",
# )
local_repository(
    name = "com_github_nanopb_nanopb",
    path = "../nanopb",
)

load("@com_github_nanopb_nanopb//extra/bazel:nanopb_deps.bzl", "nanopb_deps")

nanopb_deps()

load("@rules_python//python:repositories.bzl", "py_repositories")

py_repositories()
# http_archive(
#     name = "rules_python",
#     sha256 = "5fa3c738d33acca3b97622a13a741129f67ef43f5fdfcec63b29374cc0574c29",
#     strip_prefix = "rules_python-0.9.0",
#     url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.9.0.tar.gz",
# )

load("@com_github_nanopb_nanopb//extra/bazel:python_deps.bzl", "nanopb_python_deps")
# load("@python_versions//:defs.bzl", "interpreter")

# load("@python_3_12//:defs.bzl", "interpreter")

http_archive(
    name = "rules_python_nanopb",
    sha256 = "5fa3c738d33acca3b97622a13a741129f67ef43f5fdfcec63b29374cc0574c29",
    strip_prefix = "rules_python-0.9.0",
    url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.9.0.tar.gz",
)

load("@rules_python_nanopb//python:repositories.bzl", "python_register_toolchains")

python_register_toolchains(
    name = "python3_9",
    python_version = "3.9",
)

load("@python3_9//:defs.bzl", "interpreter")

nanopb_python_deps(interpreter)

nanopb_python_deps(interpreter)

load("@com_github_nanopb_nanopb//extra/bazel:nanopb_workspace.bzl", "nanopb_workspace")

nanopb_workspace()
