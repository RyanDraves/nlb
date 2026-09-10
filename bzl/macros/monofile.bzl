"""Single-file, self-reproducing HTML app packaging."""

load("@rules_rust_wasm_bindgen//:defs.bzl", "rust_wasm_bindgen")
load("//bzl/rules:monofile.bzl", "monofile_bundle")

def _monofile_html_impl(name, visibility, wasm_lib, shell, boot, payload, content_type, **kwargs):
    # No `platform_transition_filegroup` here, unlike the apps under `apps/`:
    # `rust_wasm_bindgen` applies its own `wasm_bindgen_transition` to
    # `wasm_file` (see its private/transitions.bzl), so wrapping it in an outer
    # transition just forks an extra configuration for nothing.
    rust_wasm_bindgen(
        name = name + "_bindgen",
        # `web` emits an ES module. Verified that an inline `<script
        # type="module">` executes on a `file://` page in Chrome 152, booting a
        # 1.29 MB Leptos client from an inlined gzip+base64 payload.
        target = "web",
        target_arch = "wasm32",
        wasm_file = wasm_lib,
        **kwargs
    )

    monofile_bundle(
        name = name,
        bindgen = name + "_bindgen",
        boot = boot,
        content_type = content_type,
        payload = payload,
        shell = shell,
        visibility = visibility,
        **kwargs
    )

monofile_html = macro(
    implementation = _monofile_html_impl,
    doc = """A single `.html` holding a wasm app, its JS glue, and a document.

    Opened from a `file://` URL the page can rewrite its own file in place via
    the File System Access API, so saving a copy is how you make a new document.
    Produces `<name>.html`.

    The app crate must `include_str!` the *same* `shell` file it is bundled with
    (wire it up as `compile_data`), because the running app rebuilds the file
    from that template plus the three inert nodes it reads back out of its own
    document.

    Monofile apps must not use `#[wasm_bindgen(inline_js = ...)]` or
    `#[wasm_bindgen(module = ...)]`: wasm-bindgen emits those as separate files
    under `snippets/` that the glue then imports, which cannot be inlined. The
    bundler rejects any glue containing an external import.
    """,
    attrs = {
        "boot": attr.label(
            allow_single_file = [".js"],
            default = Label("//lrb/monofile:boot.js"),
            doc = "Boot tail concatenated onto the glue.",
            # Prevent receiving a `select` object on the input
            configurable = False,
        ),
        "content_type": attr.string(
            default = "application/octet-stream",
            doc = "MIME type recorded in the payload frame.",
            configurable = False,
        ),
        "payload": attr.label(
            allow_single_file = True,
            doc = "Initial document. Omit for an empty payload.",
            configurable = False,
        ),
        "shell": attr.label(
            allow_single_file = [".html"],
            default = Label("//lrb/monofile:shell.html"),
            doc = "HTML shell template with the three `{{MONOFILE_*}}` placeholders.",
            configurable = False,
        ),
        "wasm_lib": attr.label(
            mandatory = True,
            doc = "The wasm32-only `rust_shared_library` (cdylib) to bundle.",
            configurable = False,
        ),
    },
)
