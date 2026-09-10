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
  System Access shim, handle persistence, and the toast. Also exported as
  `lrb_monofile::DEFAULT_SHELL`.
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

## Saving

`web::save` always writes a draft to IndexedDB first — cheap insurance on every
browser — and then:

| | Ctrl+S (`save`) | Ctrl+Shift+S (`export`) |
|---|---|---|
| Chromium | writes your actual file, clears the draft | Save As... |
| Firefox / Safari | keeps the draft only, no file created | downloads a copy |

On load, `web::current_document` returns the draft if one survived, with a flag
so the app can say "Restored unsaved changes" rather than silently showing
different content than the file holds. A download deliberately does *not* clear
the draft: the file the user has open is still the stale one, so their edits
have to survive reopening it. Only an in-place write clears it, because only
then does the file actually match.

Apps call `web::set_dirty(true)` on edit; the shell warns on tab close while
dirty. Drafts and handles are keyed by `origin + pathname` and the core asks for
`navigator.storage.persist()` so they are not evicted.

## Size

`monofile_html` runs `wasm-opt` (from `@multitool//tools/wasm-opt`, pinned in
`//tools:multitool.lock.json`) between wasm-bindgen and bundling, then the
bundler gzips the module and base64s it; `boot.js` undoes that with the native
`DecompressionStream`. Both steps matter a lot, because every byte here ends up
base64'd inside a file people pass around:

| | raw wasm | final `.html` |
|---|---|---|
| `notes_sys`, no wasm-opt | 776,329 | 285,776 |
| `notes_sys` | 319,291 | **203,259** |
| `notes_leptos`, no wasm-opt | 1,535,825 | 461,374 |
| `notes_leptos` | 499,464 | **299,969** |

`wasm-opt -Oz` alone takes 33-39% off the finished file, well beyond what
`--codegen=opt-level=z` manages on its own. Set `opt_level = ""` to skip it.

## Constraints

- **No `#[wasm_bindgen(inline_js = ...)]` or `module = "..."`.** wasm-bindgen
  emits those as separate files under `snippets/` which the glue then `import`s,
  and an external import cannot be inlined. Shared JS goes in the shell template
  and is bound as a global. The bundler fails the build on any external import.
- **Save-in-place is Chromium-only, and will stay that way.** Firefox and Safari
  implement `FileSystemFileHandle.createWritable` (FF 111, Safari 26) but ship
  *no* route to a handle for a user-visible file: no `showSaveFilePicker`, no
  `showOpenFilePicker`, no `showDirectoryPicker`, and no
  `DataTransferItem.getAsFileSystemHandle`. Their handles only address the
  sandboxed Origin Private File System. Mozilla's standards position on the File
  System Access API is *negative*
  ([#154](https://github.com/mozilla/standards-positions/issues/154)), with a
  separate *defer* on the OPFS subset they did ship
  ([#738](https://github.com/mozilla/standards-positions/issues/738)); the
  picker half is still WICG-experimental. Design around it rather than waiting.

  So `web::save` does not manufacture a file there. It persists a draft and says
  so; `web::export` is the deliberate act that produces a `.html`. That turns
  "a new file per save" into "a new file per share".
- **The first Ctrl+S for a given file always prompts.** A page cannot derive a
  `FileSystemFileHandle` for its own file, so the user must pick it once and
  confirm the overwrite. After that the handle is cached in memory *and* in
  IndexedDB, so later visits cost one permission click rather than another trip
  through the file picker.
- **Every `file://` page shares one storage origin.** Chrome buckets them all as
  `file__0`, so the saved handle is keyed by `origin + pathname`; otherwise two
  monofiles in the same Downloads folder would overwrite each other's target.
- **`showSaveFilePicker` needs transient user activation**, so `web::save`
  acquires the write target *before* rendering the file. Serializing a
  multi-megabyte document first would consume the activation. `requestPermission`
  on a restored handle has the same requirement, and is called from the same
  place for the same reason.
- **Feedback is the core's job, not each app's.** `web::save` flashes its own
  outcome via `show_toast`, so every monofile makes Ctrl+S visible without
  having to remember to.
