# Self Hosting & API Instructions
These instructions are for friends to host their own Euchre server without setting up some of the infrastructure my deployment plumbs into (e.g. `setec`). A serviceable `docker-compose.yaml` file and these steps should be detailed enough.

# Security Notice
The site is not robust in its security posture. It's backed by a site-wide password for access (something you make up and share with friends) with individual sessions being secured by the site's secret token. For access, the site is shared over [Tailscale Funnel](https://tailscale.com/docs/features/tailscale-funnel), making it publically available to you, your friends, and the entire world. The site password can almost certainly be brute forced by said world. If you browse the Tailscale logs long enough, you'll see dragnet crawlers start to poke at your site as the publically available DNS entry tells them where to find your site.

All that said, just take the server down when you're done playing. Consider not running it from a device storing files or secrets you care a lot about.

# Self Hosting Steps
The following prerequisites are required:
- You have access to a terminal (Linux/MacOS/WSL for Windows)
- You can run a Docker Compose file
- You have a Tailscale account

1. Setup filesystem: Create a directory for the server configuration, copy the `docker-compose.yaml` file & `ts-serve` folder, & create secret files. The following commands will do:
```bash
cd /my/project/dir
mkdir euc && cd euc
# Copy `docker-compose.yaml` and `ts-serve/ts-serve.json` into this directory
touch euc.authkey euc.password euc.token_secret
chmod 600 euc.authkey euc.password euc.token_secret
```
The directory should look like this (from running `tree .`):
```bash
.
├── docker-compose.yaml
├── euc.authkey
├── euc.password
├── euc.token_secret
└── ts-serve
    └── ts-serve.json
```
2. Provision password & token secret: open `euc.password` and think of a passphrase that you'll share with others. For `euc.token_secret`, run `openssl rand -base64 32` and paste in the result.
3. Setup Tailscale Funnel: We'll first setup access controls so [Tailscale Funnel](https://tailscale.com/docs/features/tailscale-funnel) can be turned on. From the [Tags section of the access controls](https://console.tailscale.com/admin/acls/visual/tags), create a new tag named `euc` owned by `autogroup:admin`. From the [Node attributes page](https://console.tailscale.com/admin/acls/visual/node-attributes), add a new node attribute that targets `tag:euc` with attribute `funnel`. The JSON preview should look like:
```json
{
	"target": ["tag:euc"],
	"attr":   ["funnel"],
}
```
4. Provision auth key: In the [key settings](https://console.tailscale.com/admin/settings/keys), create a new auth key. Enable tags for the key and select `tag:euc` for the key. Generate the key and copy it into `euc.authkey`.
5. The server can now be started with `docker compose up`.

## Tailnet-only Hosting
The `ts-serve/ts-serve.json` file contains the following by default:
```json
"AllowFunnel": {
    "${TS_CERT_DOMAIN}:443": true
}
```

To serve the site internally on your Tailnet, simple set this boolean to `false`. You can even do this while the server is running. Public access will be blocked, which is less useful for sharing with others.

# API Instructions
In the parent folder, [PROTOCOL.md](../PROTOCOL.md) describes the server's API. A minimal example of making a bot to play Euchre is in [bot.py](bot.py).
