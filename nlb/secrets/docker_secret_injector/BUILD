load("@rules_go//go:def.bzl", "go_binary", "go_library", "go_test")

go_binary(
    name = "docker_secret_injector",
    embed = [":docker_secret_injector_lib"],
    visibility = ["//visibility:public"],
)

go_test(
    name = "docker_secret_injector_test",
    srcs = ["docker_secret_injector_test.go"],
    embed = [":docker_secret_injector_lib"],
)

go_library(
    name = "docker_secret_injector_lib",
    srcs = ["docker_secret_injector.go"],
    importpath = "nlb/nlb/secrets/docker_secret_injector",
    visibility = ["//visibility:private"],
)
