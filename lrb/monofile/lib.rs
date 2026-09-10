//! Core for "monofile" apps: a whole web app and its document in one `.html`
//! file that rewrites itself when you save it.
//!
//! Inspired by [bento](https://github.com/nyblnet/bento), but Rust/wasm and
//! document-format-agnostic, so the same core carries a slide deck (`apps/dek`),
//! a diagram, or a notes scratchpad. A monofile holds three inert parts — the
//! wasm-bindgen glue, the gzipped base64 wasm module, and the document payload —
//! and the running app rebuilds the entire file from them on save.
//!
//! Everything here is pure string and byte handling, so it builds and is tested
//! on the host; the DOM and File System Access glue lives in `web.rs` behind
//! `#[cfg(target_arch = "wasm32")]`.

pub mod payload;
pub mod shell;

/// The stock shell template, which is also `monofile_html`'s default.
///
/// The running app must render from the *same* template the bundler used, so
/// apps on the default shell pass this to [`web::save`]. An app supplying its
/// own `shell` to `monofile_html` should `include_str!` that file instead and
/// wire it up as `compile_data`.
pub const DEFAULT_SHELL: &str = include_str!("shell.html");

pub use payload::{Payload, PayloadError};
pub use shell::{Parts, ShellError};

#[cfg(target_arch = "wasm32")]
pub mod web;
