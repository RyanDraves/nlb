load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")

py_package(
    name = "all_python_modules",
    packages = [
        "nlb",
    ],
    # Update via `tools/release/python/update_build.sh`
    # or https://github.com/RyanDraves/nlb/actions/workflows/python_release.yaml
    deps = [
        "//nlb/arduino:client",
        "//nlb/authentik:client",
        "//nlb/authentik:nlb_invite",
        "//nlb/buffham",
        "//nlb/buffham:bh",
        "//nlb/buffham:cpp_generator",
        "//nlb/buffham:engine",
        "//nlb/buffham:parser",
        "//nlb/buffham:py_generator",
        "//nlb/buffham:schema_bh",
        "//nlb/buffham:template_generator",
        "//nlb/datastructure:bidirectional_dict",
        "//nlb/github:nlb_gh_feature",
        "//nlb/hyd:progress_bar",
        "//nlb/mcp:arduino",
        "//nlb/mcp:arduino_mcp",
        "//nlb/mcp:file_edit",
        "//nlb/mcp:file_edit_mcp",
        "//nlb/mcp:tool_manager",
        "//nlb/mcp:util",
        "//nlb/models:model",
        "//nlb/models/blockworld",
        "//nlb/models/blockworld:blockworld_plot",
        "//nlb/models/blockworld:blockworld_sample_mdp",
        "//nlb/models/blockworld:closed_loop_llm",
        "//nlb/models/blockworld:environment",
        "//nlb/models/blockworld:heuristic",
        "//nlb/models/blockworld:heuristic_llm",
        "//nlb/models/blockworld:mdp",
        "//nlb/models/blockworld:mdp_llm",
        "//nlb/models/blockworld:mdp_manual",
        "//nlb/models/blockworld:metrics",
        "//nlb/models/blockworld:open_loop_llm",
        "//nlb/models/blockworld:plot",
        "//nlb/secrets",
        "//nlb/sharetrace",
        "//nlb/sharetrace:__init__",
        "//nlb/sharetrace:interface",
        "//nlb/sharetrace:sharetrace_demo",
        "//nlb/sharetrace:st",
        "//nlb/tailscale:nlb_tailscale",
        "//nlb/util:click_utils",
        "//nlb/util:console_utils",
        "//nlb/util:dataclass",
        "//nlb/util:dataframe",
        "//nlb/util:exception",
        "//nlb/util:introspection",
        "//nlb/util:path_utils",
        "//nlb/util:prompt_utils",
        "//nlb/util:semantic_errors",
        "//nlb/util:test_utils",
        "//nlb/util:timeout",
        "//nlb/util:timer",
        "//nlb/util:venv_completions",
        "//nlb/util:version",
        "//nlb/wizaidry:audio_util",
        "//nlb/wizaidry:text_handler",
        "//nlb/wizaidry:util",
        "//nlb/wizaidry:voice_handler",
    ],
)

py_wheel(
    name = "nlb_wheel",
    # Update via `tools/release/python/update_build.sh`
    # or https://github.com/RyanDraves/nlb/actions/workflows/python_release.yaml
    data_files = {
        "//nlb/buffham:buffham_completions": "data/share/completions/buffham-completion.bash",
        "//nlb/github:nlb_gh_feature_completions": "data/share/completions/nlb_gh_feature-completion.bash",
        "//nlb/tailscale:nlb_tailscale_completions": "data/share/completions/nlb_tailscale-completion.bash",
        "//nlb/util:venv_completions_completions": "data/share/completions/venv_completions-completion.bash",
        "//nlb/authentik:nlb_invite_completions": "data/share/completions/nlb_invite-completion.bash",
        "//nlb/mcp:arduino_mcp_completions": "data/share/completions/arduino_mcp-completion.bash",
        "//nlb/mcp:file_edit_mcp_completions": "data/share/completions/file_edit_mcp-completion.bash",
        "//nlb/sharetrace:sharetrace_completions": "data/share/completions/sharetrace-completion.bash",
        "//nlb/sharetrace:sharetrace_demo_completions": "data/share/completions/sharetrace_demo-completion.bash",
        "//nlb/models/blockworld:blockworld_completions": "data/share/completions/blockworld-completion.bash",
        "//nlb/models/blockworld:blockworld_plot_completions": "data/share/completions/plot-completion.bash",
    },
    description_file = "pypi_README.md",
    distribution = "nl_blocks",  # Unfortunate PyPI name collision
    # Update via `tools/release/python/update_build.sh`
    # or https://github.com/RyanDraves/nlb/actions/workflows/python_release.yaml
    entry_points = {"console_scripts": [
        "arduino_mcp = nlb.mcp.arduino_mcp:main",
        "blockworld = nlb.models.blockworld.blockworld:main",
        "blockworld_plot = nlb.models.blockworld.blockworld_plot:main",
        "buffham = nlb.buffham.buffham:main",
        "file_edit_mcp = nlb.mcp.file_edit_mcp:main",
        "nlb_gh_feature = nlb.github.nlb_gh_feature:main",
        "nlb_invite = nlb.authentik.nlb_invite:main",
        "nlb_tailscale = nlb.tailscale.nlb_tailscale:main",
        "sharetrace = nlb.sharetrace.sharetrace:main",
        "sharetrace_demo = nlb.sharetrace.sharetrace_demo:main",
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
