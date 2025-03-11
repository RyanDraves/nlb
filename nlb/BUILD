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
        "//nlb/buffham",
        "//nlb/buffham:bh",
        "//nlb/buffham:cpp_generator",
        "//nlb/buffham:engine",
        "//nlb/buffham:parser",
        "//nlb/buffham:py_generator",
        "//nlb/buffham:template_generator",
        "//nlb/datastructure:bidirectional_dict",
        "//nlb/hyd:progress_bar",
        "//nlb/tailscale:wrapper",
        "//nlb/util:click_utils",
        "//nlb/util:console_utils",
        "//nlb/util:dataclass",
        "//nlb/util:exception",
        "//nlb/util:path_utils",
        "//nlb/util:prompt_utils",
    ],
)

# bazel run --stamp --embed_label=0.0.3 -- //nlb:nlb_wheel.publish --repository testpypi
py_wheel(
    name = "nlb_wheel",
    description_file = "pypi_README.md",
    distribution = "nlb",
    python_tag = "py3",
    # Looser requirements than the lockfile
    requires_file = "//:requirements.txt",
    twine = "@publish_deps//twine",
    version = "{BUILD_EMBED_LABEL}",
    deps = [
        ":all_python_modules",
    ],
)
