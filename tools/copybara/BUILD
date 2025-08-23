load("@rules_java//java:java_binary.bzl", "java_binary")

java_binary(
    name = "sharetrace",
    args = [
        "$(location :copy.bara.sky)",
    ],
    data = [
        ":copy.bara.sky",
    ],
    main_class = "com.google.copybara.Main",
    runtime_deps = ["@copybara//jar"],
)
