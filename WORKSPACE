workspace(name = "nlb")

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

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

# Zmq

http_archive(
    name = "cppzmq",
    build_file = "//bzl/deps:cppzmq.BUILD",
    integrity = "sha256-VNXYMV/WEWEkrH7sQRYQriFlLcpwwLyTbbXyzM9K1gs=",
    patch_args = ["-p1"],
    patches = ["//bzl/deps:cppzmq.patch"],
    strip_prefix = "cppzmq-4.10.0",
    url = "https://github.com/zeromq/cppzmq/archive/refs/tags/v4.10.0.zip",
)

http_archive(
    name = "libzmq",
    build_file = "//bzl/deps:libzmq.BUILD",
    integrity = "sha256-SbnWzRInXZSidyT82mRlVPE68nhX4/53i3LLJFx0l24=",
    strip_prefix = "libzmq-4.3.5",
    url = "https://github.com/zeromq/libzmq/archive/refs/tags/v4.3.5.zip",
)

# esp-idf

# TODO: Make this useful
git_repository(
    name = "esp-idf",
    # v5.3.1 tag
    commit = "c8fc5f643b7a7b0d3b182d3df610844e3dc9bd74",
    remote = "https://github.com/espressif/esp-idf.git",
)
