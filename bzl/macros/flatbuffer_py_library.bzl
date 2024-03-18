load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@com_github_google_flatbuffers//:build_defs.bzl", "flatbuffer_library_public")

def flatbuffer_py_library(name, srcs, outs, **kwargs):
    flatbuffer_library_public(
        name = name + "_internal",
        srcs = srcs,
        outs = outs,
        language_flag = "--python",
        flatc_args = [
            "--gen-object-api",
            "--gen-compare",
            "--no-includes",
            "--gen-mutable",
            "--reflect-names",
            "--gen-onefile",
            "--python-typing",
        ],
        **kwargs
    )

    py_library(
        name = name,
        srcs = outs,
    )
