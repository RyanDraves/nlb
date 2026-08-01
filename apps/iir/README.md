# iir — "Is it raining in Boulder, CO?"

axum server + Leptos wasm client. The server
proxies OpenWeatherMap so the API key stays server-side.

## Dev
- Get an OpenWeatherMap API key. Provide it via either:
  - `OPENWEATHER_API_KEY=<key>` in the environment, or
  - `OPENWEATHER_API_KEY_FILE=<path>` pointing at a file with the key.
- `OPENWEATHER_API_KEY=<key> bazel run //apps/iir:serve` (listens on
  `IIR_PORT`, default 3000).
- Without a key, `/api/weather` returns `{"error": "API key not configured"}`.

## Prod
- `bazel run //apps/iir:iir_amd64_load` to build & load the image locally, or
  `bazel run //apps/iir:iir_push` to push to ghcr.
- From `/services/iir`: `docker compose -f docker-compose.yaml up -d`.
