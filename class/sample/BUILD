load("@aspect_bazel_lib//lib:write_source_files.bzl", "write_source_file")
load("@bazel_latex//:latex.bzl", "latex_document")

latex_document(
    name = "sample",
    srcs = [
        "transfer.png",
        "@bazel_latex//packages:biblatex",
        "@bazel_latex//packages:graphicx",
        "@bazel_latex//packages:hyperref",
    ],
    bib_tool = "biber",
    format = "pdf",
    main = "main.tex",
)

# This is just to commit an example; not expected to be used
write_source_file(
    name = "sample_pdf",
    in_file = "sample.pdf",
    out_file = "sample.pdf",
)
