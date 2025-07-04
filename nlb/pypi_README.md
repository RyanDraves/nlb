Hello, nlb!

This is a packaged release of the Python `nlb` modules in the namesake [nlb](https://github.com/RyanDraves/nlb) monorepo. Due to unfortunate naming collisions, this package is published as `nl-blocks` on PyPI, however it is imported as its canonical `nlb` name.

You may need `apt` packages to install the required packages. Browse through `APT_PACKAGES` in [setup.sh](https://github.com/RyanDraves/nlb/blob/main/setup.sh#L31). `portaudio19-dev` is a likely suspect.

Docs? No thanks. Here's a simple directory tree until ReadTheDocs is setup:

nlb<br />
├── arduino -> Client wrappers for the Arduino CLI<br />
├── buffham -> Serialization & RPC library<br />
├── datastructure -> Datastructure implementations<br />
├── github -> Github utilities<br />
├── hyd -> Fancy progress bars<br />
├── models -> Toy problems for algorithmic development (mostly `.gitignore`'d)<br />
├── tailscale -> Tailscale utilities<br />
├── util -> Utilities<br />
└── wizaidry -> Library for creating proto-Agentic AI wizards<br />

`wizaidry` has its own [blog post](https://ryandraves.com/posts/wizaidry), which can serve as a Getting Started page.
