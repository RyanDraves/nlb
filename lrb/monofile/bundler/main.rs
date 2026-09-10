//! Build-time bundler: shell template + wasm-bindgen output + document ->
//! one self-contained `.html`.
//!
//! Deliberately built on the same `lrb_monofile::shell::render` the wasm app
//! calls when the user saves. Because both sides share one implementation, the
//! `render(render(x)) == render(x)` property is structural, and this binary
//! asserts it on every build (see `verify`) — so a shell template that cannot
//! reproduce itself fails the build rather than shipping.

use std::path::{Path, PathBuf};
use std::process::ExitCode;

use lrb_monofile::payload::{gzip_base64, looks_precompressed};
use lrb_monofile::shell::{self, Parts};
use lrb_monofile::Payload;

const USAGE: &str = "\
usage: monofile_bundler --shell F --glue F --boot F --wasm F --out F
                        [--content-type T] [--payload F]

  --shell         HTML template containing the three {{MONOFILE_*}} placeholders
  --glue          wasm-bindgen JS glue (target=web)
  --boot          boot tail, concatenated onto the glue
  --wasm          the .wasm module, gzipped and base64'd into the file
  --out           output .html
  --content-type  MIME type recorded in the payload frame
                  (default: application/octet-stream)
  --payload       initial document; omit for an empty payload
";

fn main() -> ExitCode {
    match run() {
        Ok(summary) => {
            println!("{summary}");
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("monofile_bundler: {e}");
            ExitCode::FAILURE
        }
    }
}

#[derive(Default)]
struct Args {
    shell: Option<PathBuf>,
    glue: Option<PathBuf>,
    boot: Option<PathBuf>,
    wasm: Option<PathBuf>,
    out: Option<PathBuf>,
    payload: Option<PathBuf>,
    content_type: Option<String>,
}

fn parse_args() -> Result<Args, String> {
    let mut args = Args::default();
    let mut it = std::env::args().skip(1);
    while let Some(flag) = it.next() {
        let mut value = || {
            it.next()
                .ok_or_else(|| format!("{flag} needs a value\n\n{USAGE}"))
        };
        match flag.as_str() {
            "--shell" => args.shell = Some(value()?.into()),
            "--glue" => args.glue = Some(value()?.into()),
            "--boot" => args.boot = Some(value()?.into()),
            "--wasm" => args.wasm = Some(value()?.into()),
            "--out" => args.out = Some(value()?.into()),
            "--payload" => args.payload = Some(value()?.into()),
            "--content-type" => args.content_type = Some(value()?),
            "-h" | "--help" => return Err(USAGE.to_owned()),
            other => return Err(format!("unknown flag {other}\n\n{USAGE}")),
        }
    }
    Ok(args)
}

fn require(v: Option<PathBuf>, name: &str) -> Result<PathBuf, String> {
    v.ok_or_else(|| format!("missing {name}\n\n{USAGE}"))
}

fn read(path: &Path) -> Result<Vec<u8>, String> {
    std::fs::read(path).map_err(|e| format!("reading {}: {e}", path.display()))
}

fn read_text(path: &Path) -> Result<String, String> {
    String::from_utf8(read(path)?).map_err(|e| format!("{} is not utf-8: {e}", path.display()))
}

fn run() -> Result<String, String> {
    let args = parse_args()?;
    let shell_path = require(args.shell, "--shell")?;
    let out_path = require(args.out, "--out")?;

    let template = read_text(&shell_path)?;
    shell::validate_template(&template)
        .map_err(|e| format!("{}: {e}", shell_path.display()))?;

    let glue = read_text(&require(args.glue, "--glue")?)?;
    reject_external_imports(&glue)?;

    let boot = read_text(&require(args.boot, "--boot")?)?;
    let wasm = read(&require(args.wasm, "--wasm")?)?;

    let document = match &args.payload {
        Some(p) => read(p)?,
        None => Vec::new(),
    };
    let content_type = args
        .content_type
        .unwrap_or_else(|| "application/octet-stream".to_owned());

    // Compressing an already-compressed document (a pptx is a deflated zip)
    // costs time and saves nothing, so only bother when it actually helps.
    let compress_document = !looks_precompressed(&document);

    let parts = Parts {
        glue: format!("{glue}\n{boot}"),
        wasm: gzip_base64(&wasm),
        payload: Payload::new(content_type, document.clone()).encode(compress_document),
    };

    let html = shell::render(&template, &parts).map_err(|e| e.to_string())?;
    verify(&template, &html, &parts)?;

    std::fs::write(&out_path, &html)
        .map_err(|e| format!("writing {}: {e}", out_path.display()))?;

    Ok(format!(
        "{}: {} bytes (wasm {} -> {} base64, document {} -> {})",
        out_path.display(),
        html.len(),
        wasm.len(),
        parts.wasm.len(),
        document.len(),
        parts.payload.len(),
    ))
}

/// Assert on every build that the file we just produced can reproduce itself.
///
/// A monofile that renders correctly once but drifts on the second generation
/// is worse than one that fails outright, because the corruption shows up only
/// after a user has saved their work.
fn verify(template: &str, html: &str, parts: &Parts) -> Result<(), String> {
    let recovered = shell::parse(html)
        .map_err(|e| format!("rendered file does not parse back: {e}"))?;
    if recovered != parts.normalized() {
        return Err("rendered file does not round-trip to the parts it was built from".to_owned());
    }
    let gen2 = shell::render(template, &recovered).map_err(|e| e.to_string())?;
    if gen2 != html {
        return Err(format!(
            "render is not a fixed point: gen1 is {} bytes, gen2 is {} bytes",
            html.len(),
            gen2.len()
        ));
    }
    Ok(())
}

/// wasm-bindgen emits `#[wasm_bindgen(inline_js)]` and `module = "..."` interop
/// as separate files under `snippets/` which the glue then imports. An external
/// import silently breaks single-file bundling — the app would load, then fail
/// on the first call into the missing module — so refuse to build instead.
fn reject_external_imports(glue: &str) -> Result<(), String> {
    for (n, line) in glue.lines().enumerate() {
        let t = line.trim_start();
        // Match a module *specifier* (`from "..."`), not the bare word "from".
        // `export function f() { /* pulled from the cache */ }` is ordinary
        // code, and refusing to build on it would be a maddening false alarm.
        let has_specifier = t.contains(" from \"") || t.contains(" from '");
        let is_import = t.starts_with("import \"")
            || t.starts_with("import '")
            || ((t.starts_with("import ") || t.starts_with("import{") || t.starts_with("import("))
                && has_specifier)
            || (t.starts_with("export ") && has_specifier);
        if is_import {
            return Err(format!(
                "glue line {} imports an external module, which cannot be inlined:\n  {}\n\
                 monofile apps must not use #[wasm_bindgen(inline_js = ...)] or \
                 #[wasm_bindgen(module = ...)]; put shared JS in the shell template instead.",
                n + 1,
                t.trim_end()
            ));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn flags_external_imports_but_allows_plain_exports() {
        // What wasm-bindgen target=web actually ends its glue with.
        assert!(reject_external_imports("export { initSync, __wbg_init as default };").is_ok());
        assert!(reject_external_imports("const x = 1;\nfunction f() {}").is_ok());
        // A string mentioning import is not an import.
        assert!(reject_external_imports("const s = 'import foo';").is_ok());

        assert!(reject_external_imports("import * as x from './snippets/a.js';").is_err());
        assert!(reject_external_imports("  import {a} from 'b';").is_err());
        assert!(reject_external_imports("export { x } from './snippets/a.js';").is_err());
        assert!(reject_external_imports("import './snippets/a.js';").is_err());
    }

    /// Blocking a legitimate build is worse than the thing being guarded
    /// against, because the guard is unconditional and the failure is baffling.
    #[test]
    fn does_not_flag_the_word_from_inside_ordinary_code() {
        for ok in [
            "export function decode(b) { /* copied from the spec */ }",
            "export const msg = 'read from disk';",
            "export function pick(a) { return a.from | 0; }",
            "// import from somewhere",
        ] {
            assert!(
                reject_external_imports(ok).is_ok(),
                "false positive on: {ok}"
            );
        }
    }

    /// `verify` is what makes the fixed point structural rather than hoped for,
    /// so it needs to actually reject a file that does not round-trip.
    #[test]
    fn verify_accepts_a_good_render_and_rejects_a_tampered_one() {
        let template = concat!(
            "<html><body>",
            "<script id=\"monofile-wasm\">{{MONOFILE_WASM}}</script>",
            "<script id=\"monofile-payload\">{{MONOFILE_PAYLOAD}}</script>",
            "<script id=\"monofile-glue\">{{MONOFILE_GLUE}}</script>",
            "</body></html>",
        );
        let parts = Parts {
            glue: "const a = 1;".to_owned(),
            wasm: "H4sIAAAA".to_owned(),
            payload: "TU9OTwEA".to_owned(),
        };
        let html = shell::render(template, &parts).unwrap();
        verify(template, &html, &parts).unwrap();

        let tampered = html.replace("H4sIAAAA", "H4sIAAAB");
        assert!(verify(template, &tampered, &parts).is_err());
    }

    #[test]
    fn detects_precompressed_documents() {
        assert!(looks_precompressed(b"PK\x03\x04rest of a pptx"));
        assert!(looks_precompressed(b"\x1f\x8bgzip"));
        assert!(looks_precompressed(b"\x89PNG\r\n"));
        assert!(!looks_precompressed(b"plain text"));
        assert!(!looks_precompressed(b""));
    }
}
