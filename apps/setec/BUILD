load("@tar.bzl//tar:tar.bzl", "tar")
load("//bzl/macros:go_image.bzl", "go_image")

# Package the docker_secret_injector binary into a tarball for the OCI image
tar(
    name = "injector_app_layer",
    srcs = ["//nlb/secrets/docker_secret_injector"],
    mtree = [
        "./opt/injector type=file content=$(execpath {})".format("//nlb/secrets/docker_secret_injector:docker_secret_injector"),
    ],
)

go_image(
    name = "setec",
    additional_tars = [":injector_app_layer"],
    # Opinionated default args
    args = [
        "-verbose",
        "--",
        "/opt/app",
        "server",
    ],
    binary = "@com_github_tailscale_setec//cmd/setec",
    entrypoint = "/opt/injector",
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
