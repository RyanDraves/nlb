# Secrets

- OpenAI key
  - `openai.key`
  - Provisioned at https://platform.openai.com/settings/organization/api-keys
- Lobe Chat password
  - `lobe_chat.password`
  - Used to unlock Lobe Chat service
  - Arbitrary password; sync with password manager to use in web UI
- Portainer token
  - `portainer.token`
  - Access token for Portainer's API
  - Used by Homer for pretty homepage things
- TLS certs
  - `[host].barn-arcturus.ts.net.[crt|key]`
  - Created through Tailscale magic
  - `tailscale cert` from each `[host]`; 90 day expiry
