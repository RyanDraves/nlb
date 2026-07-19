#!/usr/bin/env bash
# Launches the euc server with its web bundle (index.html + wasm client)
# resolved from runfiles, so `bazel run //apps/euc:serve` Just Works.
# Override the port with EUC_PORT.
set -euo pipefail

RF="${RUNFILES_DIR:-${0}.runfiles}"
export EUC_WEB_DIR="${RF}/_main/apps/euc/web_bundle"
exec "${RF}/_main/apps/euc/server/server" "$@"
