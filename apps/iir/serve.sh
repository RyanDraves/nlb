#!/usr/bin/env bash
# Launches the iir server with its web bundle (index.html + wasm client)
# resolved from runfiles, so `bazel run //apps/iir:serve` Just Works.
# Override the port with IIR_PORT; set OPENWEATHER_API_KEY[_FILE] for live data.
set -euo pipefail

RF="${RUNFILES_DIR:-${0}.runfiles}"
export IIR_WEB_DIR="${RF}/_main/apps/iir/web_bundle"
exec "${RF}/_main/apps/iir/server/server" "$@"
