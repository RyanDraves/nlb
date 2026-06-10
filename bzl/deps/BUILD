# Platform-selected prebuilt libzmq, built by the `cache-and-release` repo
alias(
    name = "libzmq",
    actual = select({
        "@platforms//os:macos": "@libzmq_macos_arm64//:libzmq",
        "//conditions:default": "@libzmq_linux_x86_64//:libzmq",
    }),
    visibility = ["//visibility:public"],
)
