"""Macro for Go OCI images

From https://github.com/bazel-starters/go/blob/c3cc3dbc982bc8e26f222e586c40f314a44e42af/tools/oci/go_image.bzl#L4
and `js_image.bzl` in this repo.
"""

load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_filegroup")
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_image_index", "oci_load", "oci_push")
load("@tar.bzl//tar:tar.bzl", "tar")

def go_image(name, binary, args, platform_names, labels, local_tags, remote_repo, remote_tags, base = "@distroless_base", additional_tars = [], entrypoint = "/opt/app", **kwargs):
    """Multi-arch OCI image for a Go binary.

    Creates:
        {name}_image: The unplatformed image for the Go binary.
        {name}_{platform_name}: The platformed image for the Go binary.
        {name}_{platform_name}_load: The local load for the platformed image.
        {name}_index: The index for the multi-arch image.
        {name}_image_push: The remote push for the multi-arch image.
          - NOTE: Must login to remote repo via Docker first

    Args:
        name: The name of the image.
        binary: The name of the Go binary to run.
        args: The arguments to pass to the Go binary.
        platform_names: A list of tuples containing the platform name and the platform.
        local_tags: A list of tags to use for the local loads of the image.
        labels: Labels file to use for the image.
        remote_repo: The remote repository to push the image to.
        remote_tags: A list of tags to use for the remote pushes of the image.
        base: The base image to use for the OCI image. Defaults to "@distroless_base".
        additional_tars: A list of additional tar files to include in the image.
        entrypoint: The entrypoint for the OCI image. Defaults to "/opt/app".
        **kwargs: Additional arguments to pass to the all rules.
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
        labels = labels,
        cmd = args,
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

    # Push the image to the remote repo, e.g. the GitHub Container Registry
    oci_push(
        name = "{}_push".format(name),
        image = ":{}_index".format(name),
        remote_tags = remote_tags,
        repository = "{0}/{1}".format(remote_repo, name),
        **kwargs
    )
