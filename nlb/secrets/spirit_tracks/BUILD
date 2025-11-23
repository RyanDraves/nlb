load("@rules_go//go:def.bzl", "go_binary", "go_library")

go_binary(
    name = "spirit_tracks",
    embed = [":spirit_tracks_lib"],
    visibility = ["//visibility:public"],
)

go_library(
    name = "spirit_tracks_lib",
    srcs = ["spirit_tracks.go"],
    importpath = "nlb/nlb/secrets/spirit_tracks",
    visibility = ["//visibility:private"],
    deps = ["@com_github_tailscale_setec//client/setec"],
)
