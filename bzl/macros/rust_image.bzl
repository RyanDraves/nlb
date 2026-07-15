"""Macro for Rust OCI images.

Mirrors `go_image.bzl`, adding `env` and `exposed_ports` so a service can be
configured at the image level (the Rust services here read their config from the
environment). Unlike Go, a Rust binary that links libc must be cross-compiled
with a real cc toolchain — build these targets with `--config=image`, which adds
the hermetic Zig toolchains (see //:MODULE.bazel and .bazelrc).
"""

load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_filegroup")
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_image_index", "oci_load", "oci_push")
load("@tar.bzl//tar:tar.bzl", "tar")

def rust_image(
        name,
        binary,
        platform_names,
        local_tags,
        remote_repo,
        remote_tags,
        args = None,
        labels = None,
        env = None,
        exposed_ports = None,
        base = "@distroless_base",
        additional_tars = [],
        entrypoint = "/opt/app",
        **kwargs):
    """Multi-arch OCI image for a Rust binary.

    Creates:
        {name}_image: The unplatformed image for the Rust binary.
        {name}_{platform_name}: The platformed image for the Rust binary.
        {name}_{platform_name}_load: The local load for the platformed image.
        {name}_index: The index for the multi-arch image.
        {name}_push: The remote push for the multi-arch image.
          - NOTE: Must login to the remote repo via Docker first.

    Args:
        name: The name of the image.
        binary: The Rust binary target to run (packaged at `entrypoint`).
        platform_names: A list of (platform_name, platform) tuples.
        local_tags: Repo tags for the local loads of the image.
        remote_repo: The remote repository to push the image to.
        remote_tags: Tags to use for the remote pushes of the image.
        args: Default command args for the container (list or file). Optional.
        labels: Image labels (dict or file). Optional.
        env: Default environment variables (dict or file). Optional.
        exposed_ports: Ports the container exposes (list or file). Optional.
        base: The base image. Defaults to "@distroless_base".
        additional_tars: Extra tar layers to include (e.g. static assets).
        entrypoint: The container entrypoint. Defaults to "/opt/app".
        **kwargs: Additional arguments passed to all rules.
    """
    tar(
        name = name + "_app_layer",
        srcs = [binary],
        mtree = [
            "./opt/app type=file content=$(execpath {})".format(binary),
        ],
        **kwargs
    )

    oci_image(
        name = name + "_image",
        base = base,
        tars = [
            name + "_app_layer",
        ] + additional_tars,
        entrypoint = [
            entrypoint,
        ],
        cmd = args,
        labels = labels,
        env = env,
        exposed_ports = exposed_ports,
        visibility = ["//visibility:public"],
        **kwargs
    )

    for platform_name, platform in platform_names:
        platform_transition_filegroup(
            name = "{0}_{1}".format(name, platform_name),
            srcs = [name + "_image"],
            target_platform = platform,
        )

        oci_load(
            name = "{0}_{1}_load".format(name, platform_name),
            image = ":{0}_{1}".format(name, platform_name),
            repo_tags = local_tags,
            **kwargs
        )

    oci_image_index(
        name = "{}_index".format(name),
        images = [
            ":{0}_{1}".format(name, platform_name)
            for platform_name, _ in platform_names
        ],
        **kwargs
    )

    # Push the multi-arch index to the remote repo (e.g. GitHub Container Registry).
    oci_push(
        name = "{}_push".format(name),
        image = ":{}_index".format(name),
        remote_tags = remote_tags,
        repository = "{0}/{1}".format(remote_repo, name),
        **kwargs
    )
