#!/bin/bash

# Script to test updates to the BCR repo locally. Only meant to work on my machine;
# update `file://` otherwise.

bazel shutdown && bazel build --enable_bzlmod --registry="file:///home/dravesr/src/bazel-central-registry" \
    --lockfile_mode=off @ryandraves_nlb//nlb/buffham:buffham
