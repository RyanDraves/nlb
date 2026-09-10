//! Browser side of a monofile: read the inert parts back out of the document,
//! and rebuild the whole file when the user saves.
//!
//! Compiled only for wasm32. Everything interesting about the file format lives
//! in the pure `shell` and `payload` modules, so this stays thin — it is the
//! part that cannot be unit tested on the host, and therefore the part worth
//! keeping small.
//!
//! The File System Access calls are not made from Rust. They live in
//! `window.__monofile` in the shell template and are bound here as globals:
//! `#[wasm_bindgen(inline_js = ...)]` would make wasm-bindgen emit a separate
//! file under `snippets/` that the glue then imports, which cannot be inlined
//! into a single file.

use wasm_bindgen::prelude::*;

use crate::payload::{looks_precompressed, Payload};
use crate::shell::{self, Parts, GLUE_ID, PAYLOAD_ID, WASM_ID};

#[wasm_bindgen]
extern "C" {
    /// False on Firefox and Safari, where every save downloads a new copy.
    #[wasm_bindgen(js_namespace = __monofile, js_name = canSaveInPlace)]
    fn can_save_in_place_js() -> bool;

    /// Must be called first in a Ctrl+S handler, before any rendering work:
    /// `showSaveFilePicker` needs transient user activation, and serializing a
    /// multi-megabyte file takes long enough to lose it. Returns false if the
    /// user cancelled the picker.
    #[wasm_bindgen(js_namespace = __monofile, catch)]
    async fn acquire(options: JsValue) -> Result<JsValue, JsValue>;

    #[wasm_bindgen(js_namespace = __monofile, catch)]
    async fn commit(html: &str, options: JsValue) -> Result<JsValue, JsValue>;

    #[wasm_bindgen(js_namespace = __monofile, catch)]
    async fn open(accept: &str) -> Result<JsValue, JsValue>;

    #[wasm_bindgen(js_namespace = __monofile)]
    fn banner(text: &str);
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Saved {
    /// Written straight back over the file the user picked.
    InPlace,
    /// Downloaded as a new copy, because the browser has no File System Access.
    Downloaded,
    Cancelled,
}

#[derive(Debug)]
pub enum WebError {
    NoDocument,
    MissingNode(&'static str),
    Shell(shell::ShellError),
    Payload(crate::PayloadError),
    Js(String),
}

impl std::fmt::Display for WebError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::NoDocument => write!(f, "no document"),
            Self::MissingNode(id) => write!(f, "missing inert node #{id}"),
            Self::Shell(e) => write!(f, "{e}"),
            Self::Payload(e) => write!(f, "{e}"),
            Self::Js(e) => write!(f, "{e}"),
        }
    }
}

fn js_err(v: JsValue) -> WebError {
    WebError::Js(
        v.as_string()
            .or_else(|| js_sys::Reflect::get(&v, &"message".into()).ok().and_then(|m| m.as_string()))
            .unwrap_or_else(|| format!("{v:?}")),
    )
}

fn document() -> Result<web_sys::Document, WebError> {
    web_sys::window().and_then(|w| w.document()).ok_or(WebError::NoDocument)
}

/// Text content of one inert node.
///
/// `text_content` rather than `first_child().node_value()` on purpose: the HTML
/// parser may split a long run of characters into several sibling text nodes,
/// so reading only the first child silently truncates a large wasm payload —
/// intermittently, depending on how the file happened to be chunked off disk.
fn read_node(id: &'static str) -> Result<String, WebError> {
    document()?
        .get_element_by_id(id)
        .ok_or(WebError::MissingNode(id))
        .map(|el| el.text_content().unwrap_or_default().trim().to_owned())
}

/// The three parts of the running file, read back out of its own document.
///
/// This is what makes reproduction possible: the wasm module's own base64 is
/// still sitting untouched in the node it booted from.
pub fn current_parts() -> Result<Parts, WebError> {
    Ok(Parts {
        glue: read_node(GLUE_ID)?,
        wasm: read_node(WASM_ID)?,
        payload: read_node(PAYLOAD_ID)?,
    })
}

/// The document this file was opened with. An empty payload is not an error —
/// it is what a freshly built monofile ships with.
pub fn current_payload() -> Result<Payload, WebError> {
    let text = read_node(PAYLOAD_ID)?;
    Payload::decode(&text).map_err(WebError::Payload)
}

pub fn can_save_in_place() -> bool {
    can_save_in_place_js()
}

/// Show a persistent notice. Used to explain the download fallback on browsers
/// without the File System Access API.
pub fn show_banner(text: &str) {
    banner(text);
}

/// Rebuild the entire file around `document` and write it out.
///
/// `template` must be the same shell the bundler used — `include_str!` it and
/// wire the file up as `compile_data`. Rendering from a compile-time constant,
/// rather than from the live DOM, is what keeps generations byte-identical:
/// `documentElement.outerHTML` would capture rendered app state and normalize
/// attribute quoting, so gen-2 would differ from gen-1.
pub async fn save(
    template: &str,
    document: &Payload,
    force_picker: bool,
) -> Result<Saved, WebError> {
    // Acquire the write target BEFORE rendering; see `acquire` above.
    let opts = js_sys::Object::new();
    js_sys::Reflect::set(&opts, &"forcePicker".into(), &force_picker.into())
        .map_err(js_err)?;
    if !acquire(opts.into()).await.map_err(js_err)?.is_truthy() {
        return Ok(Saved::Cancelled);
    }

    // A pptx is an already-deflated zip; gzipping it again costs time and saves
    // nothing, so only compress what actually shrinks.
    let compress = !looks_precompressed(&document.data);
    let parts = Parts { payload: document.encode(compress), ..current_parts()? };
    let html = shell::render(template, &parts).map_err(WebError::Shell)?;

    let result = commit(&html, JsValue::UNDEFINED).await.map_err(js_err)?;
    Ok(match result.as_string().as_deref() {
        Some("downloaded") => Saved::Downloaded,
        _ => Saved::InPlace,
    })
}

/// Ask the user for a file. `accept` is an `<input accept=...>` list, e.g.
/// `".pptx,.potx"`. `Ok(None)` means they cancelled.
pub async fn open_file(accept: &str) -> Result<Option<(String, Vec<u8>)>, WebError> {
    let picked = open(accept).await.map_err(js_err)?;
    if picked.is_falsy() {
        return Ok(None);
    }
    let name = js_sys::Reflect::get(&picked, &"name".into())
        .map_err(js_err)?
        .as_string()
        .unwrap_or_default();
    let bytes = js_sys::Reflect::get(&picked, &"bytes".into()).map_err(js_err)?;
    Ok(Some((name, js_sys::Uint8Array::new(&bytes).to_vec())))
}

