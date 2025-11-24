load("//bzl/macros:go_image.bzl", "go_image")

go_image(
    name = "spirit_tracks",
    args = [],
    binary = "//nlb/secrets/spirit_tracks",
    labels = ":labels.txt",
    local_tags = ["ghcr.io/ryandraves/spirit_tracks:latest"],
    platform_names = [
        ("arm64", "//bzl/platforms:linux_arm64"),
        ("amd64", "//bzl/platforms:linux_amd64"),
    ],
    remote_repo = "ghcr.io/ryandraves",
    remote_tags = [
        "latest",
    ],
    # Too big for CI
    tags = ["manual"],
)
