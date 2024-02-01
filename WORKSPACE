workspace(name = "nlb")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

# Pico

http_archive(
    name = "rules_pico",
    url = "https://github.com/RyanDraves/rules_pico/archive/refs/heads/hermetic-toolchain.zip",
    integrity = "sha256-eYlQxBLVx4ZKuAU0ptpjc7X13BnYGHIWA76bymUVVLA=",
    strip_prefix = "rules_pico-hermetic-toolchain",
)

load("@rules_pico//pico:repositories.bzl", "rules_pico_dependencies", "rules_pico_toolchains")

rules_pico_dependencies()
rules_pico_toolchains()

http_archive(
    name = "pico-examples",
    build_file = "//pico/pico:BUILD.pico-examples",
    urls = [
        "https://github.com/raspberrypi/pico-examples/archive/refs/tags/sdk-1.4.0.tar.gz",
    ],
    strip_prefix = "pico-examples-sdk-1.4.0",
    sha256 = "a07789d702f8e6034c42e04a3f9dda7ada4ae7c8e8d320c6be6675090c007861",
)

# Arm toolchain

git_repository(
    name = "arm_none_eabi",
    commit = "4f3f31d629259e65e98b3aa7d8cb8c916cf7e03c",
    remote = "https://github.com/hexdae/bazel-arm-none-eabi",
)

load("@arm_none_eabi//:deps.bzl", "arm_none_eabi_deps")

arm_none_eabi_deps()
