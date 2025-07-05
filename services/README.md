# Self Hosted Services
Cool `docker compose`-backed self-hosted services. Most are self-explanatory, but a few deserve some documentation.

## Tailscale
Tailscale runs as a [sidecar container](https://tailscale.com/blog/docker-tailscale-guide) to provide TLS certs and expose each service at its nice URL. The [funnel feature](https://tailscale.com/kb/1223/funnel) lets these services be shared to the wider world, as desired.

Currently the certs expire every 90 days and I have to remember to bounce that Docker compose stack to re-provision them.

# Overleaf
https://overleaf.barn-arcturus.ts.net

[Overleaf Community Edition](https://github.com/overleaf/overleaf) provides a self-hosted Overleaf instance that must run on an x96 machine.

NOTE: The container starts with a minimal set of TeXLive dependencies and must be [provisioned with scheme-full](https://shihabkhan1.github.io/overleaf/stepbystep.html#upgrading-texlive) (or one-by-one if that's your thing). This takes like an hour.

TODO: Create new image per the above link
```
tlmgr install scheme-full
apt update
apt install python3-pip
python -m pip install latexminted
```

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
sudo tailscale cert pinter.barn-arcturus.ts.net
sudo cat pinter.barn-arcturus.ts.net.crt pinter.barn-arcturus.ts.net.key > pinter.barn-arcturus.ts.net.pem
sudo chmod 600 pinter.barn-arcturus.ts.net.pem
# Open /etc/haproxy/haproxy.cfg and make sure `frontend public` points its SSL config to `/home/pi/.octoprint/ssl/pinter.barn-arcturus.ts.net.pem`
```

## OctoPrint
[OctoPrint](https://octoprint.org/) provides a nice web UI for remote access and management of the 3D printer.
