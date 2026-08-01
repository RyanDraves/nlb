#!/usr/bin/env bash
# Launches the brm server with its web bundle (index.html + JS loaders + the
# wasm client) resolved from runfiles, so `bazel run //apps/brm:serve` Just Works
# on Linux/Mac. Override port/seed with BRM_PORT / BRM_SEED.
set -euo pipefail

RF="${RUNFILES_DIR:-${0}.runfiles}"
export BRM_WEB_DIR="${RF}/_main/apps/brm/web_bundle"
exec "${RF}/_main/apps/brm/server/server" "$@"
