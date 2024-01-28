load("//rules_jekyll:jekyll.bzl", "jekyll_site")

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "sources",
    srcs = glob(["_posts/**/*", "_layouts/**/*", "_config.yml", "about.markdown", "index.markdown", "404.html"]),
)

jekyll_site(
    name = "site",
    srcs = [":sources"],
    jekyll = "@bundle//bin:jekyll",
    config = ":_config.yml",
)
