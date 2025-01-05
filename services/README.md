# Self Hosted Services
Lazy `docker compose`-backed self-hosted services.

# Laptop Host

https://recuv-laptop.barn-arcturus.ts.net

## Portainer Server
The [Portainer](https://www.portainer.io/) server provides a nice web UI to manage and monitor services. It's not featured enough to link in any automation, but it provides quick insight into the system.

Portainer is [started up manually](https://docs.portainer.io/start/install-ce/server/docker/linux) without any special configuration.

## Nginx
[nginx](https://nginx.org/) is setup as a reverse proxy to access other services on convenient URLs. It also deals with the TLS certs.

## Lobe Chat
[LobeChat](https://lobehub.com/) is a self-hosted portal for AI chat. It provides simple access to a few bucks' worth of OpenAI credits so I can use DALLE on demand when the free stuff hits rate limits.

## Homer

[Homer](https://github.com/bastienwirtz/homer) provides a nice home page / portal for the services.
