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
        "//nlb/buffham:testdata/other_bh_py",
        "//nlb/buffham:testdata/sample_bh_py",
        "//nlb/datastructure:bidirectional_dict",
        "//nlb/hyd:progress_bar",
        "//nlb/tailscale:wrapper",
        "//nlb/util:click_utils",
        "//nlb/util:console_utils",
        "//nlb/util:dataclass",
        "//nlb/util:exception",
        "//nlb/util:introspection",
        "//nlb/util:path_utils",
        "//nlb/util:prompt_utils",
        "//nlb/util:secrets",
        "//nlb/util:semantic_errors",
        "//nlb/wizaidry:audio_util",
        "//nlb/wizaidry:text_handler",
        "//nlb/wizaidry:tool_manager",
        "//nlb/wizaidry:util",
        "//nlb/wizaidry:voice_handler",
    ],
)

# bazel run --config pypi_test --embed_label=0.0.7 -- //nlb:nlb_wheel.publish --repository testpypi
# bazel run --config pypi --embed_label=0.2.0 -- //nlb:nlb_wheel.publish --repository pypi
py_wheel(
    name = "nlb_wheel",
    data_files = {},  # TODO: Add completion data for click entrypoints
    description_file = "pypi_README.md",
    distribution = "nl_blocks",  # Unfortunate PyPI name collision
    # TODO: Query `py_binary` entrypoints and generate this dictionary
    entry_points = {"console_scripts": [
        "buffham = nlb.buffham.buffham:main",
        "nlb_tailscale = nlb.tailscale.wrapper:main",
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
