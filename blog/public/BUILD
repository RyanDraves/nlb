load("@aspect_rules_js//js:defs.bzl", "js_library")

js_library(
    name = "public",
    srcs = [".nojekyll"] + glob([
        "favicon/*",
        "assets/**/*",
    ]),
    visibility = ["//blog:__subpackages__"],
)
