load("@aspect_rules_js//js:defs.bzl", "js_image_layer")
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_load")
load("//bzl/rules:platform_transition.bzl", "platform_transition")

# TODO: Make macro less ugly, add docstring
def js_image(js_binary, platform_names):
    pkg_dir = native.package_name()

    for platform_name, platform in platform_names:
        js_binary_platform = js_binary.format(platform_name)

        js_image_layer(
            name = "next_image_layer_{}".format(platform_name),
            binary = js_binary_platform,
            platform = platform,
            root = "/app",
        )

        oci_image(
            name = "image_{}_unplatformed".format(platform_name),
            # Since js_binary depends on bash we have to bring in a base image that has bash
            base = "@debian",
            # This is `/[js_image_layer 'root']/[package name]/[js_image_layer 'binary']`
            cmd = [
                "/app/{0}/{1}".format(pkg_dir, js_binary_platform),
                "start",
            ],
            entrypoint = ["bash"],
            labels = ":labels.txt",
            tars = [
                ":next_image_layer_{}".format(platform_name),
            ],
            visibility = ["//visibility:public"],
            workdir = "/app/{0}/{1}.runfiles/_main".format(pkg_dir, js_binary_platform),
        )

        platform_transition(
            name = "image_{}".format(platform_name),
            dep = ":image_{}_unplatformed".format(platform_name),
            target_platform = platform,
        )

        # Export the image to local Docker daemon
        oci_load(
            name = "image_{}_load".format(platform_name),
            image = ":image_{}".format(platform_name),
            repo_tags = ["hyd:latest"],
        )
