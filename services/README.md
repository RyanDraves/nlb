# Self Hosted Services
Lazy `docker compose`-backed self-hosted services.

# Laptop Host
https://recuv-laptop.barn-arcturus.ts.net

## Portainer Server
The [Portainer](https://www.portainer.io/) server provides a nice web UI to manage and monitor services. It's not featured enough to link in any automation, but it provides quick insight into the system.

Portainer is [started up manually](https://docs.portainer.io/start/install-ce/server/docker/linux) without any special configuration.

# Overleaf
https://overleaf.barn-arcturus.ts.net

## Overleaf (& related services)
[Overleaf Community Edition](https://github.com/overleaf/overleaf) provides a self-hosted Overleaf instance. Note that Overleaf doesn't get to play with the other children for two reasons:
- It's unable to be served with a base URL (e.g. machine.barn-arcturus.ts.net/overleaf)
- I might use [tailscale funnel](https://tailscale.com/kb/1223/funnel) for collaboration with other folks, so isolation is good

NOTE: The container starts with a minimal set of TeXLive dependencies and must be [provisioned with scheme-full](https://shihabkhan1.github.io/overleaf/stepbystep.html#upgrading-texlive) (or one-by-one if that's your thing). This takes like an hour.

TODO: Create new image per the above link
```
tlmgr install scheme-full
apt update
apt install python3-pip
python -m pip install latexminted
```

## Tailscale
Tailscale runs as a [sidecar container](https://tailscale.com/blog/docker-tailscale-guide) to provide TLS certs and expose the service at its nice URL. The funnel feature doesn't seem to be working yet; that's a TODO for later.

# Pine
https://pine.barn-arcturus.ts.net

## Nginx
[nginx](https://nginx.org/) is setup as a reverse proxy to access other services on convenient URLs. It also deals with the TLS certs.

## Lobe Chat
[LobeChat](https://lobehub.com/) is a self-hosted portal for AI chat. It provides simple access to a few bucks' worth of OpenAI credits so I can use DALLE on demand when the free stuff hits rate limits.

## Homer
[Homer](https://github.com/bastienwirtz/homer) provides a nice home page / portal for the services.

## Portainer Agent
The [Portainer](https://www.portainer.io/) agent lets the server on the laptop host access, monitor, and manage this host.
