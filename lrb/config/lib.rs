//! Tiny config helpers shared by the Rust web apps under `apps/` (hyd, iir).

use std::env;
use std::fs;

/// Read a secret/config value from `name`, falling back to the contents of the
/// file named by `{name}_FILE`. Mirrors the `VAR` / `VAR_FILE` pattern used by
/// the Docker-secret mounts in `services/`.
///
/// Both sources are trimmed: a secret mounted from a file almost always ends
/// in a newline, and an env var set from a compose file can pick up stray
/// whitespace just as easily. A value that is empty after trimming is treated
/// as unset, so `VAR=""` with `VAR_FILE` set falls through to the file.
pub fn env_or_file(name: &str) -> Option<String> {
    if let Ok(val) = env::var(name) {
        let val = val.trim();
        if !val.is_empty() {
            return Some(val.to_owned());
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
    fn direct_env_is_trimmed() {
        env::set_var("LRB_CFG_TEST_TRIM", "  spaced  \n");
        assert_eq!(env_or_file("LRB_CFG_TEST_TRIM"), Some("spaced".to_owned()));
        env::remove_var("LRB_CFG_TEST_TRIM");
    }

    #[test]
    fn blank_env_falls_through_to_file() {
        let path = env::temp_dir().join("lrb_cfg_test_blank");
        fs::write(&path, "from-file\n").unwrap();
        env::set_var("LRB_CFG_TEST_D", "   ");
        env::set_var("LRB_CFG_TEST_D_FILE", &path);
        assert_eq!(env_or_file("LRB_CFG_TEST_D"), Some("from-file".to_owned()));
        env::remove_var("LRB_CFG_TEST_D");
        env::remove_var("LRB_CFG_TEST_D_FILE");
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
