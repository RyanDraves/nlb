# Authentik Configuration

# Secrets
To avoid the mess of hijacking entrypoints for Docker compose secrets, Authentik configuration follows the provided template to use `.env` files. The following env vars are set:
- `PG_PASS`
  - Postgres password
- `AUTHENTIK_SECRET_KEY`
  - Authentik's secret key
- `AUTHENTIK_EMAIL__PASSWORD`
  - SMTP password for Authentik's email auth

Due to poor design choices from Docker, only `.env` gets interpolated for env var substitution into the compose file, so `.public.env` is just a copy of the non-secret things, with `.env` as the source of truth.

# Flows
A hand-crafted `default-enrollment-flow.yaml` setups up user creation upon use of an invitation link.

# Policies
- `invitation_group_add.py`
  - Assign arbitrary groups a user will be added to when using a provided invite link. Example: user access to Mealie
  - Used in the enrollment Flow
