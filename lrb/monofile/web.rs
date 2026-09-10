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

use std::cell::RefCell;

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
    fn toast(text: &str, ms: u32);

    #[wasm_bindgen(js_namespace = __monofile, js_name = setDirty)]
    fn set_dirty_js(dirty: bool);

    #[wasm_bindgen(js_namespace = __monofile, js_name = isDirty)]
    fn is_dirty_js() -> bool;

    #[wasm_bindgen(js_namespace = __monofile, js_name = configure)]
    fn configure_js(opts: JsValue);

    #[wasm_bindgen(js_namespace = __monofile, js_name = newDocId)]
    fn new_doc_id() -> String;

    #[wasm_bindgen(js_namespace = __monofile, js_name = saveDraft, catch)]
    async fn save_draft_js(payload: &str) -> Result<JsValue, JsValue>;

    #[wasm_bindgen(js_namespace = __monofile, js_name = loadDraft, catch)]
    async fn load_draft_js() -> Result<JsValue, JsValue>;

    #[wasm_bindgen(js_namespace = __monofile, js_name = clearDraft, catch)]
    async fn clear_draft_js() -> Result<JsValue, JsValue>;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Saved {
    /// Written straight back over the file the user picked.
    InPlace,
    /// Kept in browser storage only. This is what Ctrl+S does on Firefox and
    /// Safari, which cannot write to the user's file at all — manufacturing a
    /// `notes(4).html` on every keystroke-save would be worse than useless.
    /// The `.html` on disk is now stale until the user exports.
    Draft,
    /// Downloaded as a new file, because the user explicitly asked to export.
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

thread_local! {
    /// This document's id for the life of the page, so `save` can stamp it onto
    /// a payload the app rebuilt from scratch.
    static DOC_ID: RefCell<String> = const { RefCell::new(String::new()) };
}

/// Name this app, once, at boot — before any save or draft call.
///
/// It scopes the IndexedDB database. Every monofile ever written is frozen code
/// still asking for the schema version it shipped with, so apps must not share
/// a database: the day one app adds a store and bumps the version, every other
/// app's files in the world would throw `VersionError` and lose their drafts,
/// unreachable and unfixable.
pub fn configure(app_id: &str) {
    let opts = js_sys::Object::new();
    let _ = js_sys::Reflect::set(&opts, &"appId".into(), &app_id.into());
    configure_js(opts.into());
}

pub fn can_save_in_place() -> bool {
    can_save_in_place_js()
}

/// Tell the core there are edits not yet written to a file, so closing the tab
/// warns instead of silently discarding them.
pub fn set_dirty(dirty: bool) {
    set_dirty_js(dirty);
}

/// Whether edits exist that are not yet written anywhere — a draft or a file.
/// Apps use it for a modified indicator; it is what the close warning reads.
pub fn is_dirty() -> bool {
    is_dirty_js()
}

/// The document to open with: a stored draft if one survived, else whatever was
/// baked into the file.
///
/// The bool is true when the draft won, so the app can say so — silently
/// resurrecting different content than the file contains would be alarming.
pub async fn current_document() -> Result<(Payload, bool), WebError> {
    let mut embedded = current_payload()?;

    // Adopt the file's id, or mint one to stamp into the next save.
    //
    // A freshly built monofile has no id: the bundler cannot assign one without
    // making its output differ on every build. So an id only reaches a file
    // once that file has been saved, and until then drafts must stay keyed by
    // path — configuring a freshly minted id here would key every draft under a
    // value that never occurs again, orphaning it on the very next load.
    //
    // Either way this must precede the draft lookup, because it decides which
    // key that lookup uses.
    let has_id = !embedded.doc_id.is_empty();
    if !has_id {
        embedded.doc_id = new_doc_id();
    }
    DOC_ID.with(|d| *d.borrow_mut() = embedded.doc_id.clone());
    if has_id {
        let opts = js_sys::Object::new();
        let _ = js_sys::Reflect::set(&opts, &"docId".into(), &embedded.doc_id.as_str().into());
        configure_js(opts.into());
    }

    let draft = load_draft_js().await.unwrap_or(JsValue::NULL);
    if draft.is_falsy() {
        return Ok((embedded, false));
    }
    let text = js_sys::Reflect::get(&draft, &"payload".into())
        .ok()
        .and_then(|v| v.as_string());
    match text.as_deref().map(Payload::decode) {
        Some(Ok(p)) => {
            // A draft equal to what the file already holds is not a restore.
            // This happens routinely: on a browser that cannot write in place,
            // Ctrl+S leaves a draft and Ctrl+Shift+S then writes a file with
            // the same content, so opening that copy would otherwise announce
            // "Restored unsaved changes" over a document that is perfectly
            // current. Drop the redundant draft while we are here.
            if p.data == embedded.data && p.content_type == embedded.content_type {
                let _ = clear_draft_js().await;
                return Ok((embedded, false));
            }
            Ok((p.with_doc_id(embedded.doc_id), true))
        }
        // A draft that will not decode is not worth failing the whole boot over.
        _ => Ok((embedded, false)),
    }
}

/// Stamp this page's document id onto a payload that has none.
///
/// Apps naturally rebuild a `Payload` from their editor state on every save,
/// which would drop the id and orphan the document's drafts on the next open.
/// Losing identity that way is silent, so the core does not rely on callers
/// remembering.
fn with_session_doc_id(document: &Payload) -> Payload {
    if !document.doc_id.is_empty() {
        return document.clone();
    }
    let id = DOC_ID.with(|d| d.borrow().clone());
    document.clone().with_doc_id(id)
}

/// Flash a short message. Transient on purpose — a permanent bar explaining the
/// download fallback is noise once you have read it once.
pub fn show_toast(text: &str) {
    toast(text, 2200);
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
    let document = &with_session_doc_id(document);
    let compress = !looks_precompressed(&document.data);
    let encoded = document.encode(compress);

    // Persist a draft first, on every browser. It costs a few ms and it is the
    // difference between "the tab crashed" and "the work is gone".
    let _ = save_draft_js(&encoded).await;

    if !can_save_in_place() {
        set_dirty_js(false);
        toast("Saved locally \u{2014} Ctrl+Shift+S to download a copy", 2600);
        return Ok(Saved::Draft);
    }

    // Acquire the write target BEFORE rendering; see `acquire` above.
    let opts = js_sys::Object::new();
    js_sys::Reflect::set(&opts, &"forcePicker".into(), &force_picker.into())
        .map_err(js_err)?;
    let purpose = if force_picker { "copy" } else { "in-place" };
    js_sys::Reflect::set(&opts, &"purpose".into(), &purpose.into()).map_err(js_err)?;
    if !acquire(opts.into()).await.map_err(js_err)?.is_truthy() {
        return Ok(Saved::Cancelled);
    }

    let parts = Parts { payload: encoded, ..current_parts()? };
    let html = shell::render(template, &parts).map_err(WebError::Shell)?;

    let result = match commit(&html, JsValue::UNDEFINED).await {
        Ok(v) => v,
        Err(e) => {
            let e = js_err(e);
            toast(&format!("Save failed: {e}"), 6000);
            return Err(e);
        }
    };

    let _ = result;
    // The file on disk now matches the document, so the draft is redundant.
    let _ = clear_draft_js().await;
    set_dirty_js(false);
    toast("Saved", 1600);
    Ok(Saved::InPlace)
}

/// Explicitly produce a `.html` file: "Save As" on Chromium, a download
/// everywhere else. This is the deliberate act of making a file to share or to
/// replace the one on disk, as opposed to [`save`], which is about not losing
/// work.
///
/// The draft is deliberately *not* cleared on a download: the file the user is
/// looking at is still the stale one, so their edits must survive reopening it.
pub async fn export(template: &str, document: &Payload) -> Result<Saved, WebError> {
    if can_save_in_place() {
        return save(template, document, true).await;
    }
    let document = with_session_doc_id(document);
    let compress = !looks_precompressed(&document.data);
    let encoded = document.encode(compress);

    // Also keep a draft. The file the user is looking at stays stale after a
    // download, so without this their edits would live only in the new copy —
    // reopening the original would silently show old content.
    let _ = save_draft_js(&encoded).await;

    let parts = Parts { payload: encoded, ..current_parts()? };
    let html = shell::render(template, &parts).map_err(WebError::Shell)?;

    match commit(&html, JsValue::UNDEFINED).await {
        Ok(_) => {
            // The edits are on disk now, so there is nothing left that exists
            // only in this tab. Warning on close after the user has just
            // written a file is worse than not warning at all: it teaches them
            // the prompt is noise.
            set_dirty_js(false);
            toast("Downloaded a copy", 2200);
            Ok(Saved::Downloaded)
        }
        Err(e) => {
            let e = js_err(e);
            toast(&format!("Download failed: {e}"), 6000);
            Err(e)
        }
    }
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

