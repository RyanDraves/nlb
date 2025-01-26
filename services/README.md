# Self Hosted Services
Lazy `docker compose`-backed self-hosted services.

# Laptop Host
https://recuv-laptop.barn-arcturus.ts.net

## Portainer Server
The [Portainer](https://www.portainer.io/) server provides a nice web UI to manage and monitor services. It's not featured enough to link in any automation, but it provides quick insight into the system.

Portainer is [started up manually](https://docs.portainer.io/start/install-ce/server/docker/linux) without any special configuration.

# Overleaf
https://overleaf.barn-arcturus.ts.net

Overleaf must run on an x86 machine (probably the laptop).

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

Raspberry Pi 4B. Acts as a host for most services. Runs a basic Raspberry Pi OS image.

## Nginx
[nginx](https://nginx.org/) is setup as a reverse proxy to access other services on convenient URLs. It also deals with the TLS certs.

## Lobe Chat
[LobeChat](https://lobehub.com/) is a self-hosted portal for AI chat. It provides simple access to a few bucks' worth of OpenAI credits so I can use DALLE on demand when the free stuff hits rate limits.

## Homer
[Homer](https://github.com/bastienwirtz/homer) provides a nice home page / portal for the services.

## Mealie
https://recipes.barn-arcturus.ts.net

[Mealie](https://mealie.io/) is a neat recipe server. It can scrape online recipes and put them into a sane format, share recipes with others, and generate shopping lists from meal plans.

A Tailscale sidecar provides TLS certs.

## Portainer Agent
The [Portainer](https://www.portainer.io/) agent lets the server on the laptop host access, monitor, and manage this host.

# Pinter
https://pinter.barn-arcturus.ts.net
https://pinter.barn-arcturus.ts.net/webcam/stream

Pinter is Raspberry Pi 3B connected to an Ender 3 3D printer. It's running the specialized OctoPi (w/ new camera stack) image, so its services are running directly on the host and not via Docker.

## HAProxy
OctoPi ships with [HAProxy](https://www.haproxy.org/) to manage TLS and routing between Octoprint and the webcam server (which are separate).

Pinter is setup with TLS certs created by Tailscale. The following steps point HAProxy to these certs:

```bash
mkdir -p ~/.octoprint/ssl
cd ~/.octoprint/ssl
sudo tailscale cert pinter.barn-arcturus.ts.net`
sudo cat pinter.barn-arcturus.ts.net.crt pinter.barn-arcturus.ts.net.key > pinter.barn-arcturus.ts.net.pem
sudo chmod 600 pinter.barn-arcturus.ts.net.pem
# Open /etc/haproxy/haproxy.cfg and make sure `frontend public` points its SSL config to `/home/pi/.octoprint/ssl/pinter.barn-arcturus.ts.net.pem`
```

## OctoPrint
[OctoPrint](https://octoprint.org/) provides a nice web UI for remote access and management of the 3D printer.
