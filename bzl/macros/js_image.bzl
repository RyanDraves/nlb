load("@aspect_rules_js//js:defs.bzl", "js_image_layer")
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_image_index", "oci_load", "oci_push")
load("//bzl/rules:platform_transition.bzl", "platform_transition")

def js_image(name, js_binary, args, platform_names, local_tags, remote_repo, remote_tags, **kwargs):
    """Multi-arch OCI image for a JS binary.

    Args:
        name: The name of the image.
        js_binary: The name of the JS binary to run.
        args: The arguments to pass to the JS binary.
        platform_names: A list of tuples containing the platform name and the platform.
        local_tags: A list of tags to use for the local loads of the image.
        remote_repo: The remote repository to push the image to.
        remote_tags: A list of tags to use for the remote pushes of the image.
        **kwargs: Additional arguments to pass to the all rules.

    Creates:
        {name}_image: The unplatformed image for the JS binary.
        {name}_{platform_name}: The platformed image for the JS binary.
        {name}_{platform_name}_load: The local load for the platformed image.
        {name}_index: The index for the multi-arch image.
        {name}_image_push: The remote push for the multi-arch image.
          - NOTE: Must login to remote repo via Docker first
    """
    pkg_dir = native.package_name()

    js_image_layer(
        name = "{}_js_image_layer".format(name),
        binary = js_binary,
        root = "/app",
        **kwargs
    )

    oci_image(
        name = "{}_image".format(name),
        # Since js_binary depends on bash we have to bring in a base image that has bash
        base = "@debian",
        # This is `/[js_image_layer 'root']/[package name]/[js_image_layer 'binary']`
        cmd = [
            "/app/{0}/{1}".format(pkg_dir, js_binary),
        ] + args,
        entrypoint = ["bash"],
        labels = ":labels.txt",
        tars = [
            ":{}_js_image_layer".format(name),
        ],
        visibility = ["//visibility:public"],
        workdir = "/app/{0}/{1}.runfiles/_main".format(pkg_dir, js_binary),
        **kwargs
    )

    for platform_name, platform in platform_names:
        platform_transition(
            name = "{0}_{1}".format(name, platform_name),
            dep = ":{}_image".format(name),
            target_platform = platform,
        )

        # Export the image to local Docker daemon
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
