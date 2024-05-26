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

# Json C++

http_archive(
    name = "nlohmann_json",
    integrity = "sha256-BAIrBdgG61/3MCPCgLaGl9Erk+G3JnoLIqGjnsdXgGk=",
    strip_prefix = "json-3.11.3",
    url = "https://github.com/nlohmann/json/archive/refs/tags/v3.11.3.zip",
)

# Picotool

load("//tools/rpi_picotool:picotool.bzl", "picotool_repository")

picotool_repository(name = "picotool")
