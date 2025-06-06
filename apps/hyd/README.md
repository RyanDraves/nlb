# Usage

## Dev
- Add a `.env` file with a `POSTGRES_PASSWORD` entry
- Add the same password to `/services/secrets/hyd_postgres.password`
- Start up the `hyd-db` service in `/services/docker-compose.hyd.yaml`
- Make sure `app/layout.tsx` has the right import
- Use `bazel run //apps/hyd:next_dev` or `pnpm dev`

## Prod
- Similar DB setup
- `bazel run //apps/hyd:hyd_amd64_load` or push to GCR with `bazel run //apps/hyd:hyd_push`
- From `/services/`: `docker compose -f docker-compose.hyd.yaml up -d`
