"""Rule that splices a wasm-bindgen bundle and a document into one .html file.

Reads `RustWasmBindgenInfo` rather than going through a `genrule`, because that
provider hands back the glue `.js` and the `.wasm` as exact `File`s. A genrule
would see the target's whole `DefaultInfo` — wasm, js, ts, and a snippets
TreeArtifact in one space-separated `$(locations)` blob — and have to sniff by
file extension.

The real work lives in `//lrb/monofile/bundler`, which shares
`lrb_monofile::shell::render` with the wasm runtime so the self-reproduction
fixed point is verified on every build.
"""

load("@rules_rust_wasm_bindgen//:defs.bzl", "RustWasmBindgenInfo")

def _monofile_bundle_impl(ctx):
    info = ctx.attr.bindgen[RustWasmBindgenInfo]

    js = info.js.to_list()
    if len(js) != 1:
        fail("expected exactly one glue .js from {}, got {}".format(
            ctx.attr.bindgen.label,
            [f.short_path for f in js],
        ))

    out = ctx.actions.declare_file(ctx.label.name + ".html")

    args = ctx.actions.args()
    args.add("--shell", ctx.file.shell)
    args.add("--glue", js[0])
    args.add("--boot", ctx.file.boot)
    args.add("--wasm", info.wasm)
    args.add("--content-type", ctx.attr.content_type)
    args.add("--out", out)

    inputs = [ctx.file.shell, ctx.file.boot, js[0], info.wasm]
    if ctx.file.payload:
        args.add("--payload", ctx.file.payload)
        inputs.append(ctx.file.payload)

    ctx.actions.run(
        executable = ctx.executable._bundler,
        arguments = [args],
        inputs = inputs,
        outputs = [out],
        mnemonic = "MonofileBundle",
        progress_message = "Bundling single-file app %{label}",
    )

    return [DefaultInfo(files = depset([out]))]

monofile_bundle = rule(
    implementation = _monofile_bundle_impl,
    doc = "Splice a `rust_wasm_bindgen` bundle and a document payload into one .html file.",
    attrs = {
        "bindgen": attr.label(
            doc = "A `rust_wasm_bindgen` target built with `target = \"web\"`.",
            providers = [RustWasmBindgenInfo],
            mandatory = True,
        ),
        "boot": attr.label(
            doc = "Boot tail appended to the glue. Defaults to the stock one.",
            allow_single_file = [".js"],
            default = Label("//lrb/monofile:boot.js"),
        ),
        "content_type": attr.string(
            doc = "MIME type recorded in the payload frame.",
            default = "application/octet-stream",
        ),
        "payload": attr.label(
            doc = "Initial document. Omit for an empty payload.",
            allow_single_file = True,
        ),
        "shell": attr.label(
            doc = "HTML shell template holding the three `{{MONOFILE_*}}` placeholders.",
            allow_single_file = [".html"],
            default = Label("//lrb/monofile:shell.html"),
        ),
        "_bundler": attr.label(
            default = Label("//lrb/monofile/bundler"),
            executable = True,
            cfg = "exec",
        ),
    },
)
