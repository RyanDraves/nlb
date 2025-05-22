load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")

py_package(
    name = "all_python_modules",
    packages = [
        "nlb",
    ],
    # Output of
    # `bazel query 'kind("py_binary", //nlb/...) + kind("py_library", //nlb/...)'`
    # Remove `testdata` targets (TODO: better query)
    deps = [
        "//nlb/arduino:client",
        "//nlb/buffham",
        "//nlb/buffham:bh",
        "//nlb/buffham:cpp_generator",
        "//nlb/buffham:engine",
        "//nlb/buffham:parser",
        "//nlb/buffham:py_generator",
        "//nlb/buffham:template_generator",
        "//nlb/datastructure:bidirectional_dict",
        "//nlb/github:nlb_gh_feature",
        "//nlb/hyd:progress_bar",
        "//nlb/tailscale:nlb_tailscale",
        "//nlb/util:click_utils",
        "//nlb/util:console_utils",
        "//nlb/util:dataclass",
        "//nlb/util:exception",
        "//nlb/util:introspection",
        "//nlb/util:path_utils",
        "//nlb/util:prompt_utils",
        "//nlb/util:secrets",
        "//nlb/util:semantic_errors",
        "//nlb/util:venv_completions",
        "//nlb/wizaidry:audio_util",
        "//nlb/wizaidry:text_handler",
        "//nlb/wizaidry:tool_manager",
        "//nlb/wizaidry:util",
        "//nlb/wizaidry:voice_handler",
    ],
)

# bazel run --config pypi_test --embed_label=0.0.12 -- //nlb:nlb_wheel.publish --repository testpypi
# bazel run --config pypi --embed_label=0.4.0 -- //nlb:nlb_wheel.publish --repository pypi
py_wheel(
    name = "nlb_wheel",
    # TODO: Query completion files and generate this dictionary
    data_files = {
        "//nlb/buffham:buffham_completions": "data/share/completions/buffham-completion.bash",
        "//nlb/github:nlb_gh_feature_completions": "data/share/completions/nlb_gh_feature.bash",
        "//nlb/tailscale:nlb_tailscale_completions": "data/share/completions/nlb_tailscale-completion.bash",
    },
    description_file = "pypi_README.md",
    distribution = "nl_blocks",  # Unfortunate PyPI name collision
    # TODO: Query `py_binary` entrypoints and generate this dictionary
    entry_points = {"console_scripts": [
        "buffham = nlb.buffham.buffham:main",
        "nlb_gh_feature = nlb.github.nlb_gh_feature:main",
        "nlb_tailscale = nlb.tailscale.nlb_tailscale:main",
        "venv_completions = nlb.util.venv_completions:main",
    ]},
    license = "MIT",
    # https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#urls
    project_urls = {
        "Repository": "https://github.com/RyanDraves/nlb",
        "Issues": "https://github.com/RyanDraves/nlb/issues",
    },
    python_requires = ">=3.12",  # Uses new type var syntax
    python_tag = "py3",
    # Looser requirements than the lockfile
    requires_file = "//:requirements.txt",
    # TODO: Add version.py file from the Bazel stamping
    stamp = -1,  # Let the `--[no]stamp` flag control stamping
    summary = "Ryan's fever dreams",
    twine = "@publish_deps//twine",
    version = "{BUILD_EMBED_LABEL}",
    deps = [
        ":all_python_modules",
    ],
)
