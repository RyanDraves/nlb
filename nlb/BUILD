load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")

py_package(
    name = "all_python_modules",
    packages = [
        "nlb",
    ],
    # Update via `tools/release/python/update_build.sh`
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
        "//nlb/util:version",
        "//nlb/wizaidry:audio_util",
        "//nlb/wizaidry:text_handler",
        "//nlb/wizaidry:tool_manager",
        "//nlb/wizaidry:util",
        "//nlb/wizaidry:voice_handler",
    ],
)

py_wheel(
    name = "nlb_wheel",
    # Update via `tools/release/python/update_build.sh`
    data_files = {
        "//nlb/buffham:buffham_completions": "data/share/completions/buffham-completion.bash",
        "//nlb/github:nlb_gh_feature_completions": "data/share/completions/nlb_gh_feature-completion.bash",
        "//nlb/tailscale:nlb_tailscale_completions": "data/share/completions/nlb_tailscale-completion.bash",
        "//nlb/util:venv_completions_completions": "data/share/completions/venv_completions-completion.bash",
    },
    description_file = "pypi_README.md",
    distribution = "nl_blocks",  # Unfortunate PyPI name collision
    # Update via `tools/release/python/update_build.sh`
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
    stamp = -1,  # Let the `--[no]stamp` flag control stamping
    summary = "Ryan's fever dreams",
    twine = "@publish_deps//twine",
    version = "{BUILD_EMBED_LABEL}",
    deps = [
        ":all_python_modules",
    ],
)
