load("//bzl/macros:go_image.bzl", "go_image")

go_image(
    name = "setec",
    args = [],
    binary = "@com_github_tailscale_setec//cmd/setec",
    labels = ":labels.txt",
    local_tags = ["ghcr.io/ryandraves/setec:latest"],
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
