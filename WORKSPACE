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

load("@rules_pico//pico:repositories.bzl", "rules_pico_dependencies", "rules_pico_toolchains")

rules_pico_dependencies()

rules_pico_toolchains()

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
    commit = "6c906b5691aa1b0ddc21094b606b3f6080f6e477",
    remote = "https://github.com/RyanDraves/bazel-arm-none-eabi",
)

load("@arm_none_eabi//:deps.bzl", "arm_none_eabi_deps")

arm_none_eabi_deps(version = "13.2.1")
