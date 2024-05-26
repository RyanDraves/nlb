"""Repo rule for picotool.

Inspired by the beautiful Bazel tooling at
https://github.com/RobotLocomotion/drake/blob/master/tools/workspace/
"""

def _impl(repo_ctx):
    repo_ctx.symlink(
        Label(":package.BUILD"),
        "BUILD",
    )

    url = "https://github.com/raspberrypi/picotool/archive/refs/tags/1.1.2.tar.gz"
    sha256 = "f1746ead7815c13be1152f0645db8ea3b277628eb0110d42a0a186db37d40a91"
    repo_ctx.download_and_extract(
        url = url,
        output = "picotool_repo",
        sha256 = sha256,
        type = "tar.gz",
        stripPrefix = "picotool-1.1.2",
    )

    url = "https://github.com/raspberrypi/pico-sdk/archive/refs/tags/1.5.1.tar.gz"
    sha256 = "95f5e522be3919e36a47975ffd3b208c38880c14468bd489ac672cfe3cec803c"
    repo_ctx.download_and_extract(
        url = url,
        output = "pico_sdk_repo",
        sha256 = sha256,
        type = "tar.gz",
        stripPrefix = "pico-sdk-1.5.1",
    )

picotool_repository = repository_rule(
    implementation = _impl,
)
