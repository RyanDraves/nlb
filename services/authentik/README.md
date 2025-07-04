# Authentik Configuration

# Secrets
To avoid the mess of hijacking entrypoints for Docker compose secrets, Authentik configuration follows the provided template to use `.env` files. The following env vars are set:
- `PG_PASS`
  - Postgres password
- `AUTHENTIK_SECRET_KEY`
  - Authentik's secret key
- `AUTHENTIK_EMAIL__PASSWORD`
  - SMTP password for Authentik's email auth

# Policies
Some (one) useful expression policies are stored here (and configured in Authentik's settings).
- `invitation_group_add.py`
  - Assign arbitrary groups a user will be added to when using a provided invite link. Example: user access to Mealie
