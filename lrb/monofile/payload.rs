//! Framing for the document blob a monofile carries in its inert `<script>` tag.
//!
//! Kept deliberately ignorant of HTML: this module turns `(content_type, bytes)`
//! into one line of base64 and back, so it is pure, host-testable, and reusable
//! by any monofile app regardless of what its document actually is. `shell.rs`
//! owns the HTML side and treats the output here as an opaque string.

use base64::engine::general_purpose::STANDARD;
use base64::Engine as _;
use std::io::{Read as _, Write as _};

/// Wire format:
///
/// ```text
/// magic   b"MONO"   4 bytes
/// version u8        1 byte   currently 1
/// flags   u8        1 byte   bit 0 = body is gzipped
/// ct_len  u16 LE    2 bytes
/// ct      utf-8     ct_len bytes
/// body    bytes     to end
/// ```
///
/// The whole frame is then base64'd. Base64's alphabet is `A-Za-z0-9+/=`, which
/// cannot produce `<`, so an encoded payload can never terminate the script tag
/// that holds it — that safety property is why the framing is binary-then-base64
/// rather than, say, JSON with an embedded string.
const MAGIC: &[u8; 4] = b"MONO";
const VERSION: u8 = 1;
const FLAG_GZIP: u8 = 1 << 0;

/// A document plus the MIME type that says how to interpret it.
///
/// For `apps/dek` the content type is the pptx one and `data` is the OPC zip;
/// for the Phase 0 demo apps it is `text/plain`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Payload {
    pub content_type: String,
    pub data: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PayloadError {
    BadBase64(String),
    BadMagic,
    UnsupportedVersion(u8),
    Truncated,
    BadContentType,
    Gunzip(String),
}

impl std::fmt::Display for PayloadError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::BadBase64(e) => write!(f, "payload is not valid base64: {e}"),
            Self::BadMagic => write!(f, "payload is missing the MONO magic"),
            Self::UnsupportedVersion(v) => write!(f, "payload version {v} is not supported"),
            Self::Truncated => write!(f, "payload frame is truncated"),
            Self::BadContentType => write!(f, "payload content type is not valid utf-8"),
            Self::Gunzip(e) => write!(f, "payload failed to decompress: {e}"),
        }
    }
}

impl std::error::Error for PayloadError {}

impl Payload {
    pub fn new(content_type: impl Into<String>, data: Vec<u8>) -> Self {
        Self { content_type: content_type.into(), data }
    }

    /// An empty payload, which is what a freshly built monofile ships with.
    ///
    /// `apps/dek` starts here: there is no blank-deck template to clone, so a
    /// new monofile holds nothing until the user imports a `.pptx`.
    pub fn empty(content_type: impl Into<String>) -> Self {
        Self::new(content_type, Vec::new())
    }

    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }

    /// Frame, optionally gzip, and base64 into the text of a payload script tag.
    ///
    /// `compress` is a caller decision because it is not always a win: pptx is
    /// an already-deflated zip, so gzipping it again costs time and saves
    /// almost nothing, while a text document compresses roughly 10:1.
    pub fn encode(&self, compress: bool) -> String {
        let body = if compress { gzip(&self.data) } else { self.data.clone() };

        let ct = self.content_type.as_bytes();
        let mut frame = Vec::with_capacity(8 + ct.len() + body.len());
        frame.extend_from_slice(MAGIC);
        frame.push(VERSION);
        frame.push(if compress { FLAG_GZIP } else { 0 });
        frame.extend_from_slice(&(ct.len() as u16).to_le_bytes());
        frame.extend_from_slice(ct);
        frame.extend_from_slice(&body);

        STANDARD.encode(&frame)
    }

    /// Inverse of [`Payload::encode`]. Tolerates surrounding whitespace, since
    /// the text comes out of an HTML node that a formatter may have indented.
    pub fn decode(text: &str) -> Result<Self, PayloadError> {
        let trimmed: String = text.split_whitespace().collect();
        if trimmed.is_empty() {
            return Err(PayloadError::Truncated);
        }
        let frame = STANDARD
            .decode(trimmed.as_bytes())
            .map_err(|e| PayloadError::BadBase64(e.to_string()))?;

        if frame.len() < 8 {
            return Err(PayloadError::Truncated);
        }
        if &frame[0..4] != MAGIC {
            return Err(PayloadError::BadMagic);
        }
        let version = frame[4];
        if version != VERSION {
            return Err(PayloadError::UnsupportedVersion(version));
        }
        let flags = frame[5];
        let ct_len = u16::from_le_bytes([frame[6], frame[7]]) as usize;

        let ct_end = 8usize.checked_add(ct_len).ok_or(PayloadError::Truncated)?;
        if frame.len() < ct_end {
            return Err(PayloadError::Truncated);
        }
        let content_type = std::str::from_utf8(&frame[8..ct_end])
            .map_err(|_| PayloadError::BadContentType)?
            .to_owned();

        let body = &frame[ct_end..];
        let data = if flags & FLAG_GZIP != 0 { gunzip(body)? } else { body.to_vec() };

        Ok(Self { content_type, data })
    }
}

/// Whether `data` already carries its own compression, so gzipping it again
/// would cost time and save nothing.
///
/// Matters because the headline case is a pptx, which is a deflated zip. Used
/// by both the build-time bundler and the running app to make the same call.
pub fn looks_precompressed(data: &[u8]) -> bool {
    // gzip, zip (pptx/docx/xlsx), png, jpeg.
    const MAGICS: [&[u8]; 4] = [b"\x1f\x8b", b"PK\x03\x04", b"\x89PNG", b"\xff\xd8\xff"];
    MAGICS.iter().any(|m| data.starts_with(m))
}

/// Gzip then base64, with no `MONO` frame around it.
///
/// This is the encoding of the wasm module slot: it is not a document, so it
/// needs no content type or version, and the browser undoes it at boot with
/// `DecompressionStream('gzip')` (see `boot.js`). Kept here so the compression
/// choice has one home.
pub fn gzip_base64(data: &[u8]) -> String {
    STANDARD.encode(gzip(data))
}

/// Inverse of [`gzip_base64`], for tests and tooling. At runtime the browser
/// does this natively rather than dragging an inflate implementation into wasm.
pub fn ungzip_base64(text: &str) -> Result<Vec<u8>, PayloadError> {
    let trimmed: String = text.split_whitespace().collect();
    let raw = STANDARD
        .decode(trimmed.as_bytes())
        .map_err(|e| PayloadError::BadBase64(e.to_string()))?;
    gunzip(&raw)
}

fn gzip(data: &[u8]) -> Vec<u8> {
    let mut enc = flate2::write::GzEncoder::new(Vec::new(), flate2::Compression::best());
    // Writing to a Vec is infallible, and GzEncoder only surfaces the sink's
    // errors, so neither of these can fail in practice.
    enc.write_all(data).expect("gzip into Vec cannot fail");
    enc.finish().expect("gzip finish into Vec cannot fail")
}

fn gunzip(data: &[u8]) -> Result<Vec<u8>, PayloadError> {
    let mut out = Vec::new();
    flate2::read::GzDecoder::new(data)
        .read_to_end(&mut out)
        .map_err(|e| PayloadError::Gunzip(e.to_string()))?;
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn roundtrip(p: &Payload, compress: bool) {
        assert_eq!(Payload::decode(&p.encode(compress)).unwrap(), *p);
    }

    #[test]
    fn roundtrips_both_compressed_and_not() {
        let p = Payload::new("text/plain", b"hello world".to_vec());
        roundtrip(&p, false);
        roundtrip(&p, true);
    }

    #[test]
    fn roundtrips_empty_payload() {
        let p = Payload::empty("application/octet-stream");
        assert!(p.is_empty());
        roundtrip(&p, false);
        roundtrip(&p, true);
    }

    #[test]
    fn roundtrips_binary_and_unicode() {
        // Arbitrary bytes, including NULs and a valid-utf8 tail, plus a content
        // type long enough to exercise the u16 length field.
        let mut data: Vec<u8> = (0u8..=255).collect();
        data.extend_from_slice("héllo 世界 \u{1F600}".as_bytes());
        let p = Payload::new(
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            data,
        );
        roundtrip(&p, false);
        roundtrip(&p, true);
    }

    #[test]
    fn encoded_text_can_never_close_a_script_tag() {
        let hostile = b"</script><script>alert(1)</script>".to_vec();
        let encoded = Payload::new("text/html", hostile.clone()).encode(false);
        assert!(!encoded.contains('<'));
        assert!(!encoded.to_ascii_lowercase().contains("script"));
        assert_eq!(Payload::decode(&encoded).unwrap().data, hostile);
    }

    #[test]
    fn tolerates_whitespace_from_html_formatting() {
        let p = Payload::new("text/plain", b"indented".to_vec());
        let pretty = format!("\n      {}\n    ", p.encode(true));
        assert_eq!(Payload::decode(&pretty).unwrap(), p);
    }

    #[test]
    fn compression_actually_compresses_repetitive_data() {
        let p = Payload::new("text/plain", "ha".repeat(5000).into_bytes());
        assert!(p.encode(true).len() * 4 < p.encode(false).len());
    }

    #[test]
    fn rejects_corrupt_frames() {
        assert_eq!(Payload::decode(""), Err(PayloadError::Truncated));
        assert_eq!(Payload::decode("   \n  "), Err(PayloadError::Truncated));
        assert!(matches!(Payload::decode("not base64!!"), Err(PayloadError::BadBase64(_))));
        assert_eq!(Payload::decode(&STANDARD.encode(b"XXXX\x01\x00\x00\x00")), Err(PayloadError::BadMagic));
        assert_eq!(Payload::decode(&STANDARD.encode(b"MONO")), Err(PayloadError::Truncated));

        let mut future = b"MONO".to_vec();
        future.extend_from_slice(&[99, 0, 0, 0]);
        assert_eq!(Payload::decode(&STANDARD.encode(&future)), Err(PayloadError::UnsupportedVersion(99)));

        // ct_len claims 64 bytes of content type that are not present.
        let mut lying = b"MONO".to_vec();
        lying.extend_from_slice(&[VERSION, 0, 64, 0]);
        assert_eq!(Payload::decode(&STANDARD.encode(&lying)), Err(PayloadError::Truncated));
    }

    #[test]
    fn gzip_base64_roundtrips_and_is_script_safe() {
        // Stand-in for a wasm module: incompressible-ish header plus a long
        // repetitive tail, so the gzip actually has work to do.
        let mut wasm = b"\0asm\x01\0\0\0".to_vec();
        wasm.extend(std::iter::repeat_n(0xABu8, 20_000));

        let encoded = gzip_base64(&wasm);
        assert!(!encoded.contains('<'));
        assert_eq!(ungzip_base64(&encoded).unwrap(), wasm);
        assert!(encoded.len() < wasm.len(), "gzip should shrink this input");
    }

    #[test]
    fn ungzip_base64_rejects_garbage() {
        assert!(matches!(ungzip_base64("!!!"), Err(PayloadError::BadBase64(_))));
        assert!(matches!(
            ungzip_base64(&STANDARD.encode(b"not gzip")),
            Err(PayloadError::Gunzip(_))
        ));
    }

    #[test]
    fn rejects_gzip_flag_over_garbage_body() {
        let mut bad = b"MONO".to_vec();
        bad.extend_from_slice(&[VERSION, FLAG_GZIP, 0, 0]);
        bad.extend_from_slice(b"not actually gzip");
        assert!(matches!(Payload::decode(&STANDARD.encode(&bad)), Err(PayloadError::Gunzip(_))));
    }
}
