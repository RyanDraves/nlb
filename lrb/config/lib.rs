//! Tiny config helpers shared by the Rust web apps under `apps/` (hyd, iir).
//!
//! Dependency-free on purpose: each app resolves third-party crates from its
//! own crate_universe hub (`@hyd_crates`, `@iir_crates`), so a crate linked by
//! more than one app must not pull external crates or the hubs would supply
//! conflicting types. See `lrb/rng` for the same constraint.

use std::env;
use std::fs;

/// Read a secret/config value from `name`, falling back to the contents of the
/// file named by `{name}_FILE` (trimmed). Mirrors the `VAR` / `VAR_FILE`
/// pattern used by the old Next.js apps (Postgres password, OpenWeather key)
/// and by the Docker-secret mounts in `services/`.
///
/// Precedence matches the historical TS behaviour: for the Postgres password
/// the file wins when set; here the direct env var wins if present, otherwise
/// the file is consulted. Both apps only ever set one or the other, so the
/// distinction is moot in practice.
pub fn env_or_file(name: &str) -> Option<String> {
    if let Ok(val) = env::var(name) {
        if !val.is_empty() {
            return Some(val);
        }
    }
    let path = env::var(format!("{name}_FILE")).ok()?;
    match fs::read_to_string(&path) {
        Ok(contents) => Some(contents.trim().to_owned()),
        Err(err) => {
            eprintln!("error reading {name}_FILE ({path}): {err}");
            None
        }
    }
}

/// Parse a `u16` port from env var `name`, falling back to `default` when the
/// var is unset or unparseable.
pub fn env_port(name: &str, default: u16) -> u16 {
    env::var(name)
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(default)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn direct_env_wins() {
        env::set_var("LRB_CFG_TEST_A", "direct");
        assert_eq!(env_or_file("LRB_CFG_TEST_A"), Some("direct".to_owned()));
        env::remove_var("LRB_CFG_TEST_A");
    }

    #[test]
    fn falls_back_to_file_trimmed() {
        let dir = env::temp_dir();
        let path = dir.join("lrb_cfg_test_secret");
        fs::write(&path, "  s3cret\n").unwrap();
        env::remove_var("LRB_CFG_TEST_B");
        env::set_var("LRB_CFG_TEST_B_FILE", &path);
        assert_eq!(env_or_file("LRB_CFG_TEST_B"), Some("s3cret".to_owned()));
        env::remove_var("LRB_CFG_TEST_B_FILE");
        fs::remove_file(&path).ok();
    }

    #[test]
    fn missing_returns_none() {
        env::remove_var("LRB_CFG_TEST_C");
        env::remove_var("LRB_CFG_TEST_C_FILE");
        assert_eq!(env_or_file("LRB_CFG_TEST_C"), None);
    }

    #[test]
    fn port_default_and_parse() {
        env::remove_var("LRB_CFG_TEST_PORT");
        assert_eq!(env_port("LRB_CFG_TEST_PORT", 3000), 3000);
        env::set_var("LRB_CFG_TEST_PORT", "8080");
        assert_eq!(env_port("LRB_CFG_TEST_PORT", 3000), 8080);
        env::set_var("LRB_CFG_TEST_PORT", "notaport");
        assert_eq!(env_port("LRB_CFG_TEST_PORT", 3000), 3000);
        env::remove_var("LRB_CFG_TEST_PORT");
    }
}
