load("//rules_jekyll:jekyll.bzl", "jekyll_site")

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "sources",
    srcs = glob([
        "_posts/**/*",
        "_layouts/**/*",
    ]) + [
        "404.html",
        "about.md",
        "index.md",
    ],
)

jekyll_site(
    name = "site",
    srcs = [":sources"],
    config = "_config.yml",
    jekyll = "@bundle//bin:jekyll",
)
