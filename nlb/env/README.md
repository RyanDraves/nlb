# What is this?
This is an environment image used for remote build execution (see `bzl/platforms/BUILD` and `.bazelrc`).

Currently, this uses the default strategy [suggested by rules_oci](https://docs.aspect.build/guides/rules_oci_migration/#1-build-base-layer): build and publish your own base image with the right system dependencies.

TODO: look into using [rules_distroless](https://github.com/GoogleContainerTools/rules_distroless) instead.
