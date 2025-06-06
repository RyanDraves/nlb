# Usage

## Setup
- Add a `.env` file to the project root with the following entry:
  ```
  OPENWEATHER_API_KEY=your_openweather_api_key
  ```

# Dev
- Add a `.env` file with a `OPENWEATHER_API_KEY` entry
- Add the same API key to `/services/secrets/iir_openweather_api.key`
- Make sure `app/layout.tsx` has the right import
- Use `bazel run //apps/iir:next_dev` or `pnpm dev`

# Prod
- `bazel run //apps/iir:iir_amd64_load` or push to GCR with `bazel run //apps/iir:iir_push`
- From `/services/hyd`: `docker compose -f docker-compose.yaml up -d`
