# monofile — self-reproducing single-file web apps

A whole Rust/wasm app plus its document in one `.html` file that rewrites itself
when you save. Inspired by [bento](https://github.com/nyblnet/bento), but Rust
and document-format-agnostic, so the same core can carry a slide deck, a
diagram, or a notes scratchpad.

Open the file from a `file://` URL, edit, press Ctrl+S, and the page writes a new
version of *itself* back over the same file. Saving a copy is how you make a new
document.

## Layout

- `payload.rs` — document framing: `(content_type, bytes)` → one line of base64.
  Pure, host-tested.
- `shell.rs` — the self-reproduction logic: splice three parts into the shell
  template and pull them back out. Pure, host-tested.
- `web.rs` — `#[cfg(target_arch = "wasm32")]` DOM and save glue.
- `shell.html` — the stock template, including the `window.__monofile` File
  System Access shim. Also exported as `lrb_monofile::DEFAULT_SHELL`.
- `boot.js` — boot tail concatenated onto the wasm-bindgen glue.
- `bundler/` — build-time tool behind `//bzl/macros:monofile.bzl`.

## Using it

```starlark
load("@rules_rust//rust:defs.bzl", "rust_shared_library")
load("//bzl/macros:monofile.bzl", "monofile_html")

rust_shared_library(
    name = "myapp_so",
    srcs = ["lib.rs"],
    edition = "2024",
    rustc_flags = ["--crate-type=cdylib", "--codegen=opt-level=z"],
    target_compatible_with = ["@platforms//cpu:wasm32"],
    deps = ["//lrb/monofile", "@crates//:wasm-bindgen"],
)

monofile_html(
    name = "myapp",
    content_type = "text/plain",
    wasm_lib = ":myapp_so",
)
```

Build the examples with `bazel build //lrb/monofile/examples/...`, then either
open the resulting `.html` straight off disk (which is the point) or serve them
over http via the `monofile-examples` entry in `.claude/launch.json`. Note that
save-in-place only works from `file://` or a secure origin.

## How reproduction works

The file holds three inert `<script>` nodes — the wasm-bindgen glue, the
gzipped-and-base64'd wasm module, and the document payload. The running app never
mutates them, so on save it can read its own module straight back out of the
document it booted from, and rebuild the whole file from the shell template plus
a new payload.

Two rules make this safe, and both are enforced rather than assumed:

- **Never serialize from the live DOM.** `documentElement.outerHTML` captures
  rendered app state, not source, and normalizes markup on the way out — gen-2
  would not match gen-1. The app renders from `DEFAULT_SHELL`, an `include_str!`
  constant, and reads only the *contents* of the three nodes.
- **`render` must be a fixed point**, not merely correct once:
  `render(render(x)) == render(x)`. A file that looks right on the first save and
  drifts on the second is worse than one that fails outright, because the damage
  only shows up after the user has done real work. `shell.rs` asserts this in
  `rust_test`, and the bundler re-asserts it on every build — the build tool and
  the browser call the same `shell::render`, so the property is structural.

Base64's alphabet cannot produce `<`, so no payload can terminate its own script
tag; `render` rejects any part that would.

## Constraints

- **No `#[wasm_bindgen(inline_js = ...)]` or `module = "..."`.** wasm-bindgen
  emits those as separate files under `snippets/` which the glue then `import`s,
  and an external import cannot be inlined. Shared JS goes in the shell template
  and is bound as a global. The bundler fails the build on any external import.
- **Save-in-place is Chromium-only.** Firefox and Safari have no
  `showSaveFilePicker`, so every save downloads a new copy; the app should say so
  via `web::show_banner`.
- **The first Ctrl+S of a session always prompts.** A page cannot derive a
  `FileSystemFileHandle` for its own file, so the user must pick it once and
  confirm the overwrite. After that the handle is cached and saves are silent
  until reload.
- **`showSaveFilePicker` needs transient user activation**, so `web::save`
  acquires the write target *before* rendering the file. Serializing a
  multi-megabyte document first would consume the activation.
