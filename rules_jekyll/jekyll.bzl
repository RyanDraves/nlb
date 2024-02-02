"""Simple Jekyll site builder and server for Bazel."""

def _jekyll_site_impl(ctx):
    config = ctx.attr.config
    config_path = ctx.expand_location("$(location {target})".format(target = config.label), targets = [config])

    build_files = depset(ctx.files.srcs)
    build_destination = "{bin_dir}/{package}/{destination}".format(bin_dir = ctx.bin_dir.path, package = ctx.label.package, destination = ctx.attr.destination)
    args = ["build", "--config", config_path, "--source", ctx.label.package, "--destination", build_destination, "--verbose"]

    output_directory = ctx.actions.declare_directory(ctx.attr.destination)

    # Build the site
    ctx.actions.run(
        inputs = build_files,
        outputs = [output_directory],
        arguments = args,
        executable = ctx.executable.jekyll,
        mnemonic = "JekyllBuild",
        env = {
            "LC_ALL": "C.UTF-8",
            "LANG": "en_US.UTF-8",
            "LANGUAGE": "en_US.UTF-8",
        },
    )

    # Compile transitive runfiles + our build files
    runfiles = ctx.runfiles(ctx.attr.config.files.to_list() + [output_directory])
    transitive_runfiles = []
    for runfiles_attr in (
        ctx.attr.deps,
        [ctx.attr.config, ctx.attr.jekyll],
    ):
        for target in runfiles_attr:
            transitive_runfiles.append(target[DefaultInfo].default_runfiles)
    runfiles = runfiles.merge_all(transitive_runfiles)

    # This relative path works nicer for `bazel run`
    servce_destination = ctx.label.package + "/_site"
    args = ["serve", "--destination", servce_destination, "--skip-initial-build", "--config", config_path]

    # rules_ruby needs RUNFILES_DIR to be set
    executable = "export RUNFILES_DIR=$(readlink -f ../)\n"
    executable += ctx.attr.jekyll.files_to_run.executable.short_path + " " + " ".join(args) + " $@\n"

    ctx.actions.write(
        output = ctx.outputs.executable,
        is_executable = True,
        content = executable,
    )

    # Collect file outputs for any dependents
    serve_files = depset(ctx.attr.config.files.to_list() + [output_directory])

    return [
        DefaultInfo(
            executable = ctx.outputs.executable,
            files = serve_files,
            runfiles = runfiles,
        ),
    ]

jekyll_site = rule(
    implementation = _jekyll_site_impl,
    executable = True,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(),
        "destination": attr.string(default = "_site"),
        "config": attr.label(allow_single_file = True, mandatory = True),
        "jekyll": attr.label(executable = True, cfg = "exec", mandatory = True),
    },
)
