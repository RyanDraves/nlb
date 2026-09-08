//! Stub lib target for the repo-root `//:Cargo.toml`.
//!
//! Cargo requires every package to declare at least one target, but that
//! manifest exists only to feed the `@crates` crate_universe hub and to give
//! Renovate a single file of Rust dependencies to update. Nothing compiles
//! this file - Bazel builds the real crates from their BUILD files.
