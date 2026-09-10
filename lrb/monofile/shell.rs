//! Assembles a complete single-file HTML app from a template plus its three
//! inlined parts, and pulls those parts back out again.
//!
//! This is the self-reproduction logic, and it is deliberately nothing but
//! string handling so it runs and is tested on the host. Crucially the *same*
//! `render` is called twice: once by the build-time bundler to produce the
//! shipped `.html`, and again at runtime by the wasm app when the user saves.
//! Sharing one implementation is what makes `render(render(x)) == render(x)`
//! structural rather than a happy accident.
//!
//! The rule this module exists to enforce: **never reconstruct the file by
//! reading the live document.** `document.documentElement.outerHTML` captures
//! rendered app state, not source. Instead the shell is an `include_str!`
//! template with explicit placeholders, and the runtime only ever reads back
//! the *contents* of the inert payload nodes — never the document's structure.

/// Placeholders the bundler and the runtime both substitute. They are wrapped
/// in `{{ }}` and namespaced so they cannot collide with app markup, and every
/// one of them must appear exactly once — see [`validate_template`].
pub const GLUE_PLACEHOLDER: &str = "{{MONOFILE_GLUE}}";
pub const WASM_PLACEHOLDER: &str = "{{MONOFILE_WASM}}";
pub const PAYLOAD_PLACEHOLDER: &str = "{{MONOFILE_PAYLOAD}}";

/// DOM ids of the inert nodes the runtime reads its own parts back out of.
///
/// The wasm can rebuild itself because its own base64 is still sitting in
/// `WASM_ID`, untouched, in the document it booted from.
pub const GLUE_ID: &str = "monofile-glue";
pub const WASM_ID: &str = "monofile-wasm";
pub const PAYLOAD_ID: &str = "monofile-payload";

const PLACEHOLDERS: [&str; 3] = [GLUE_PLACEHOLDER, WASM_PLACEHOLDER, PAYLOAD_PLACEHOLDER];

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ShellError {
    /// A placeholder appeared zero times, or more than once. Both are fatal:
    /// zero means the substitution silently did nothing, and more than one means
    /// the file would carry duplicate copies of a part and could not round-trip.
    PlaceholderCount { placeholder: &'static str, found: usize },
    /// A part contained `</script`, which would terminate its own inert tag and
    /// corrupt every subsequent generation of the file.
    PartClosesScriptTag { id: &'static str },
    /// [`extract`] could not find an inert node with the given id.
    MissingNode { id: String },
}

impl std::fmt::Display for ShellError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::PlaceholderCount { placeholder, found } => write!(
                f,
                "template must contain {placeholder} exactly once, found it {found} times"
            ),
            Self::PartClosesScriptTag { id } => {
                write!(f, "part '{id}' contains `</script`, which would break the file")
            }
            Self::MissingNode { id } => write!(f, "no inert node with id '{id}' in this document"),
        }
    }
}

impl std::error::Error for ShellError {}

/// The three inlined parts of a monofile.
///
/// `glue` is the wasm-bindgen JS, `wasm` is the gzipped-then-base64'd module,
/// `payload` is [`crate::payload::Payload::encode`] output.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Parts {
    pub glue: String,
    pub wasm: String,
    pub payload: String,
}

impl Parts {
    /// The form these parts take once written into a file and read back.
    ///
    /// [`extract`] trims, because an HTML formatter may indent a node's
    /// contents, so surrounding whitespace cannot survive a generation.
    /// [`render`] therefore trims on the way in as well, and this is the
    /// normal form both agree on: `parse(render(p)) == p.normalized()`.
    /// Without this the fixed point holds but the *first* round-trip does not,
    /// which is a confusing way to fail.
    pub fn normalized(&self) -> Self {
        Self {
            glue: self.glue.trim().to_owned(),
            wasm: self.wasm.trim().to_owned(),
            payload: self.payload.trim().to_owned(),
        }
    }
}

/// Check a template before using it. The bundler calls this so a malformed
/// shell fails the build loudly instead of producing an `.html` that cannot
/// reproduce itself.
pub fn validate_template(template: &str) -> Result<(), ShellError> {
    for placeholder in PLACEHOLDERS {
        let found = template.matches(placeholder).count();
        if found != 1 {
            return Err(ShellError::PlaceholderCount { placeholder, found });
        }
    }
    Ok(())
}

/// Substitute the three parts into the shell template.
///
/// Parts are inserted in their [`Parts::normalized`] form, so what goes in is
/// exactly what [`parse`] reads back out.
///
/// Substitution is done in one left-to-right pass rather than three chained
/// `str::replace` calls, so a part whose own text happens to contain a
/// placeholder string cannot be rewritten by a later pass.
pub fn render(template: &str, parts: &Parts) -> Result<String, ShellError> {
    validate_template(template)?;
    let parts = parts.normalized();

    for (id, part) in [
        (GLUE_ID, &parts.glue),
        (WASM_ID, &parts.wasm),
        (PAYLOAD_ID, &parts.payload),
    ] {
        if contains_script_close(part) {
            return Err(ShellError::PartClosesScriptTag { id });
        }
    }

    let mut out = String::with_capacity(
        template.len() + parts.glue.len() + parts.wasm.len() + parts.payload.len(),
    );
    let mut rest = template;
    while let Some((idx, placeholder)) = next_placeholder(rest) {
        out.push_str(&rest[..idx]);
        out.push_str(match placeholder {
            GLUE_PLACEHOLDER => &parts.glue,
            WASM_PLACEHOLDER => &parts.wasm,
            _ => &parts.payload,
        });
        rest = &rest[idx + placeholder.len()..];
    }
    out.push_str(rest);
    Ok(out)
}

/// Position and identity of the earliest placeholder in `hay`, if any.
fn next_placeholder(hay: &str) -> Option<(usize, &'static str)> {
    PLACEHOLDERS
        .iter()
        .filter_map(|p| hay.find(p).map(|i| (i, *p)))
        .min_by_key(|(i, _)| *i)
}

/// `</script` in any ASCII casing, which is what actually terminates a script
/// element as far as the HTML tokenizer is concerned.
fn contains_script_close(s: &str) -> bool {
    s.to_ascii_lowercase().contains("</script")
}

/// Pull the text content of the inert node with `id` out of a rendered file.
///
/// Only for host tests and for the bundler's own verification — the wasm
/// runtime reads these nodes through the DOM instead, because scanning your own
/// source text for a marker is exactly the fragile pattern this module avoids.
pub fn extract<'a>(html: &'a str, id: &str) -> Result<&'a str, ShellError> {
    let missing = || ShellError::MissingNode { id: id.to_owned() };
    let anchor = format!("id=\"{id}\"");
    let at = html.find(&anchor).ok_or_else(missing)?;
    let open_end = html[at..].find('>').ok_or_else(missing)? + at + 1;
    let close = html[open_end..].find("</script").ok_or_else(missing)? + open_end;
    Ok(html[open_end..close].trim())
}

/// Recover all three parts from a rendered file.
pub fn parse(html: &str) -> Result<Parts, ShellError> {
    Ok(Parts {
        glue: extract(html, GLUE_ID)?.to_owned(),
        wasm: extract(html, WASM_ID)?.to_owned(),
        payload: extract(html, PAYLOAD_ID)?.to_owned(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    const TEMPLATE: &str = concat!(
        "<!DOCTYPE html>\n<html><head><title>t</title></head><body>\n",
        "<script type=\"application/octet-stream\" id=\"monofile-wasm\">{{MONOFILE_WASM}}</script>\n",
        "<script type=\"application/octet-stream\" id=\"monofile-payload\">{{MONOFILE_PAYLOAD}}</script>\n",
        "<div id=\"app\"></div>\n",
        "<script type=\"module\" id=\"monofile-glue\">{{MONOFILE_GLUE}}</script>\n",
        "</body></html>\n",
    );

    fn parts() -> Parts {
        Parts {
            glue: "export function initSync(){}".to_owned(),
            wasm: "H4sIAAAAAAAA".to_owned(),
            payload: "TU9OTwEA".to_owned(),
        }
    }

    #[test]
    fn renders_and_parses_back() {
        let html = render(TEMPLATE, &parts()).unwrap();
        assert_eq!(parse(&html).unwrap(), parts());
        assert!(html.starts_with("<!DOCTYPE html>"));
        // Every placeholder is consumed.
        for p in PLACEHOLDERS {
            assert!(!html.contains(p), "{p} survived rendering");
        }
    }

    /// The property that actually defines "self-reproducing". A gen-1 file can
    /// look perfect while gen-2 corrupts, so assert the fixed point explicitly.
    #[test]
    fn render_is_a_fixed_point_across_generations() {
        let gen1 = render(TEMPLATE, &parts()).unwrap();
        let gen2 = render(TEMPLATE, &parse(&gen1).unwrap()).unwrap();
        let gen3 = render(TEMPLATE, &parse(&gen2).unwrap()).unwrap();
        assert_eq!(gen1, gen2);
        assert_eq!(gen2, gen3);
    }

    /// Saving a new document must change only the payload, byte for byte.
    #[test]
    fn only_the_payload_changes_when_the_document_changes() {
        let gen1 = render(TEMPLATE, &parts()).unwrap();
        let edited = Parts { payload: "TU9OTwEAdGV4dA".to_owned(), ..parts() };
        let gen2 = render(TEMPLATE, &edited).unwrap();

        assert_ne!(gen1, gen2);
        assert_eq!(parse(&gen2).unwrap().wasm, parts().wasm);
        assert_eq!(parse(&gen2).unwrap().glue, parts().glue);
        assert_eq!(gen1.len() - parts().payload.len(), gen2.len() - edited.payload.len());
    }

    /// A part containing a placeholder string must be emitted verbatim, not
    /// re-substituted by a later pass. Chained `str::replace` would fail this.
    #[test]
    fn parts_containing_placeholders_are_not_re_substituted() {
        let sneaky = Parts {
            glue: format!("/* {PAYLOAD_PLACEHOLDER} {WASM_PLACEHOLDER} */"),
            ..parts()
        };
        let html = render(TEMPLATE, &sneaky).unwrap();
        assert_eq!(parse(&html).unwrap().glue, sneaky.glue);
        assert_eq!(parse(&html).unwrap().payload, sneaky.payload);
    }

    #[test]
    fn rejects_templates_with_wrong_placeholder_counts() {
        assert_eq!(
            validate_template("<html>{{MONOFILE_WASM}}{{MONOFILE_PAYLOAD}}</html>"),
            Err(ShellError::PlaceholderCount { placeholder: GLUE_PLACEHOLDER, found: 0 })
        );
        let doubled = TEMPLATE.replace(
            "<div id=\"app\"></div>",
            "<div id=\"app\"></div>{{MONOFILE_PAYLOAD}}",
        );
        assert_eq!(
            validate_template(&doubled),
            Err(ShellError::PlaceholderCount { placeholder: PAYLOAD_PLACEHOLDER, found: 2 })
        );
    }

    #[test]
    fn rejects_parts_that_would_close_their_own_tag() {
        for bad in ["</script>", "</SCRIPT >", "x</script"] {
            let p = Parts { glue: bad.to_owned(), ..parts() };
            assert_eq!(
                render(TEMPLATE, &p),
                Err(ShellError::PartClosesScriptTag { id: GLUE_ID })
            );
        }
    }

    /// Parts carrying surrounding whitespace — the bundler's glue+boot blob
    /// ends with a newline — must still round-trip, in normalized form.
    #[test]
    fn parts_with_surrounding_whitespace_round_trip_normalized() {
        let padded = Parts {
            glue: "export function initSync(){}\n".to_owned(),
            wasm: "  H4sIAAAAAAAA  ".to_owned(),
            payload: "\n\tTU9OTwEA\n".to_owned(),
        };
        let gen1 = render(TEMPLATE, &padded).unwrap();
        assert_eq!(parse(&gen1).unwrap(), padded.normalized());

        // And the fixed point still holds from the un-normalized starting point.
        let gen2 = render(TEMPLATE, &parse(&gen1).unwrap()).unwrap();
        assert_eq!(gen1, gen2);
    }

    #[test]
    fn extract_reports_missing_nodes() {
        let html = render(TEMPLATE, &parts()).unwrap();
        assert_eq!(
            extract(&html, "nope"),
            Err(ShellError::MissingNode { id: "nope".to_owned() })
        );
    }

    /// End to end with real framing, which is how the bundler will use this.
    #[test]
    fn carries_a_real_payload_through_a_generation() {
        use crate::payload::Payload;

        let doc = Payload::new("text/plain", "héllo 世界".as_bytes().to_vec());
        let p = Parts { payload: doc.encode(true), ..parts() };
        let html = render(TEMPLATE, &p).unwrap();

        let recovered = Payload::decode(&parse(&html).unwrap().payload).unwrap();
        assert_eq!(recovered, doc);
    }
}
