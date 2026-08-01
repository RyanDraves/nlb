# hyd — progress bars

axum server + Leptos wasm client, backed by Postgres. The Python CLI in `management/` writes to the same `progress` table
directly and is unchanged.

## Dev
- Add a `.env` file with a `POSTGRES_PASSWORD` entry (or set `POSTGRES_*` /
  `DATABASE_URL` in the environment).
- Add the same password to `/services/secrets/hyd_postgres.password`.
- Start the `hyd-db` service in `/services/hyd/docker-compose.yaml`.
- `bazel run //apps/hyd:serve` (listens on `HYD_PORT`, default 3000). Connects
  to Postgres from `DATABASE_URL` or the `POSTGRES_USER/PASSWORD[_FILE]/HOST/
  PORT/DB` vars (defaults: user/db `hyd`, host `localhost`, port 5432).

## Prod
- `bazel run //apps/hyd:hyd_amd64_load` or push to ghcr with
  `bazel run //apps/hyd:hyd_push`.
- From `/services/hyd`: `docker compose -f docker-compose.yaml up -d`.
