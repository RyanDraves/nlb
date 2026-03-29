# Secrets

`setec -s https://setec.barn-arcturus.ts.net list` is source of truth on what secrets exist.

| Secret Name | Notes | Additional Notes |
|-------------|-------|------------------|
| `bookmarks/meili_master_key` | Meilisearch password | |
| `bookmarks/nextauth_secret` | Internal authentication for [Karakeep](https://github.com/karakeep-app/karakeep) | |
| `bookmarks/oidc_id` | Authentik client ID | |
| `bookmarks/oidc_secret` | Authentik client secret | |
| `bookmarks/openai_key` | OPENAI API key | |
| `chat/openai_key` | OpenAI API key | Provisioned at https://platform.openai.com/settings/organization/api-keys |
| `chat/password` | Used to unlock Lobe Chat service | Arbitrary password; sync with password manager to use in web UI |
| `dash/mealie_token` | Mealie API token | |
| `dash/octoprint_token` | Access token for Octoprint's API | |
| `dash/portainer_token` | Access token for Portainer's API | |
| `hyd/postgres_password` | DB password | |
| `iir/openweathermap_api_key` | OpenWeatherMap API key | |
| `personal/claude_key` | Anthropic API key | Provisioned at https://console.anthropic.com/settings/keys |
| `personal/gemini_key` | Google Gemini API key | Provision at https://console.cloud.google.com/apis/credentials (select correct Google account) |
| `personal/ghcr_io_pat` | PAT for Github Docker registry (push permissions) | `docker login ghcr.io` to rotate |
| `personal/pypi_test_token` | API token to publish to PyPI's test index | Provisioned at https://test.pypi.org/manage/account/ |
| `personal/pypi_token` | API token to publish to PyPI's production index | Provisioned at https://pypi.org/manage/account/ |
| `recipes/oidc_id` | tsidp client ID | |
| `recipes/oidc_secret` | tsidp client secret | |
| `recipes/postgres_password` | DB password for [Mealie](https://github.com/mealie-recipes/mealie) | |
| `recipes/smtp_password` | SMTP password for Mealie's email auth | |

## Exceptions
Authentik had a template for `.env` file usage, so some secrets are stored and documented in Authentik's service folder.
