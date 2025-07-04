# Secrets

- `claude.key`
  - Anthropic API key
  - Provisioned at https://console.anthropic.com/settings/keys
- `gemini.key`
  - Google Gemini API key
  - Provision at https://console.cloud.google.com/apis/credentials (select correct Google account)
- `ghcr.io.pat`
  - PAT for Github Docker registry (push permissions)
  - `docker login ghcr.io` to rotate
- `hyd_postgres.password`
  - DB password for HYD
- `iir_openweather_api.key`
  - OpenWeatherMap API key
- `lobe_chat.password`
  - Used to unlock Lobe Chat service
  - Arbitrary password; sync with password manager to use in web UI
- `mealie_oidc.secret`
  - Authentik client secret for the Mealie provider
- `mealie_postgres.password`
  - DB password for [Mealie](https://github.com/mealie-recipes/mealie)
- `mealie_smtp.password`
  - SMTP password for Mealie's email auth
- `mealie.token`
  - Mealie API token
  - Used by Homer for pretty homepage things
- `octoprint.token`
  - Access token for Octoprint's API
  - Used by Homer for pretty homepage things
- `openai.key`
  - OpenAI API key
  - Provisioned at https://platform.openai.com/settings/organization/api-keys
- `portainer.token`
  - Access token for Portainer's API
  - Used by Homer for pretty homepage things
- `pypi_test.token`
  - API token to publish to PyPI's test index
  - Provisioned at https://test.pypi.org/manage/account/
- `pypi.token`
  - API token to publish to PyPI's production index
  - Provisioned at https://pypi.org/manage/account/
- `[host].barn-arcturus.ts.net.[crt|key]`
  - TLS certs related through Tailscale magic
  - `tailscale cert` from each `[host]`; 90 day expiry
- `tailnet_oauth.secret`
  - Used to provision a [container as a machine on the tailnet](https://tailscale.com/kb/1282/docker#ts_socks5_server)

## Exceptions
Authentik had a template for `.env` file usage, so some secrets are stored and documented in Authentik's service folder.
