"""Simple Jekyll site Bazel macro."""

load("@aspect_bazel_lib//lib:run_binary.bzl", "run_binary")
load("@bazel_skylib//rules:write_file.bzl", "write_file")

def jekyll_site(name, config, jekyll, srcs):
    """Create a Jekyll site

    Args:
        name: Name of the site target
        config: Path to the Jekyll configuration file
        jekyll: Path to the Jekyll binary
        srcs: List of source files to include in the site
    """

    site_path = "/_site"
    if native.package_name():
        site_path = "{0}/_site".format(native.package_name())

    run_binary(
        name = name + "_build",
        srcs = [config] + srcs,
        args = [
            "build",
            "--source",
            native.package_name(),
            "--destination",
            "$(GENDIR)/{0}".format(site_path),
            "--config",
            "$(location {0})".format(config),
        ],
        env = {
            "LC_ALL": "C.UTF-8",
            "LANG": "en_US.UTF-8",
            "LANGUAGE": "en_US.UTF-8",
        },
        execution_requirements = {"no-sandbox": "1"},
        mnemonic = "JekyllBuild",
        out_dirs = [
            "_site",
        ],
        tool = jekyll,
    )

    write_file(
        name = name + "serve_file",
        out = name + "_serve_file.sh",
        content = [
            "#!/bin/bash",
            # rules_ruby needs RUNFILES_DIR to be set
            "export RUNFILES_DIR=$(readlink -f ../)",
            "EXEC_ROOT=$(pwd)",
            "$EXEC_ROOT/$1 ${@:2}",
        ],
    )

    native.sh_binary(
        name = name,
        srcs = [
            name + "_serve_file.sh",
        ],
        args = [
            "$(location {0})".format(jekyll),
            "serve",
            "--destination",
            site_path,
            "--skip-initial-build",
            "--config",
            "$(location {0})".format(config),
        ],
        data = [
            config,
            ":" + name + "_build",
            jekyll,
        ],
    )
