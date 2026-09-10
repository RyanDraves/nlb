// Boot tail for a monofile. The bundler concatenates this onto the end of the
// wasm-bindgen glue and puts the result into the single `monofile-glue` node,
// so that node's content round-trips as one opaque blob and
// `render(render(x)) == render(x)` holds. Keeping the boot here rather than in
// the shell template is what makes that work: if it lived in the template
// alongside the glue placeholder, extracting the node would return glue+boot
// and the next render would append boot a second time.
//
// This runs as part of a `<script type="module">`, which is deferred, so the
// inert payload nodes are guaranteed to be parsed by the time we look for them.

const __mono_b64 = (id) => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`monofile: missing node #${id}`);
  return el.textContent.replace(/\s+/g, "");
};

// Base64 -> bytes. Chunked because String.fromCharCode.apply blows the argument
// limit somewhere around a few hundred KB, and the wasm module is bigger.
const __mono_bytes = (b64) => {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
};

// The wasm is stored gzipped: 1.29 MB of raw wasm is 1.71 MB of base64, but
// only 328 KB gzipped-then-base64. DecompressionStream is native, so the cost
// is a few ms rather than shipping an inflate implementation.
const __mono_gunzip = async (bytes) =>
  new Response(
    new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip")),
  ).arrayBuffer();

try {
  const bytes = await __mono_gunzip(__mono_bytes(__mono_b64("monofile-wasm")));
  // Compile asynchronously and hand initSync the finished Module. initSync
  // would otherwise call `new WebAssembly.Module(bytes)` itself, which is a
  // synchronous ~1.3 MB compile that blocks the main thread for 30-100 ms.
  initSync({ module: await WebAssembly.compile(bytes) });
} catch (e) {
  document.body.innerHTML =
    '<pre style="padding:1rem;font:13px/1.5 ui-monospace,monospace;color:#c00">' +
    "monofile failed to start:\n\n" +
    String(e && e.stack ? e.stack : e).replace(/[<&]/g, (c) =>
      c === "<" ? "&lt;" : "&amp;",
    ) +
    "</pre>";
  throw e;
}
