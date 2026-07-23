#!/usr/bin/env bash
# Launches the hyd server with its web bundle (index.html + wasm client)
# resolved from runfiles, so `bazel run //apps/hyd:serve` Just Works.
# Override the port with HYD_PORT; set POSTGRES_* / DATABASE_URL for the DB.
set -euo pipefail

RF="${RUNFILES_DIR:-${0}.runfiles}"
export HYD_WEB_DIR="${RF}/_main/apps/hyd/web_bundle"
exec "${RF}/_main/apps/hyd/server/server" "$@"
