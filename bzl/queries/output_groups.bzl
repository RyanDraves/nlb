# From https://stackoverflow.com/a/61282031
# Usage:
#  bazel build --nobuild //:target --aspects=bzl/queries/output_groups.bzl%output_group_query_aspect
def _output_group_query_aspect_impl(target, ctx):
    for og in target.output_groups:
        print("output group " + str(og) + ": " + str(getattr(target.output_groups, og)))
    return []

output_group_query_aspect = aspect(
    implementation = _output_group_query_aspect_impl,
)
