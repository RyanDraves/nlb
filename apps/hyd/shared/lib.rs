//! Wire types shared by the hyd server and its Leptos wasm client. Mirrors the
//! `progress` table (see `apps/hyd/management/schema.py`) and the JSON shapes
//! the old Next.js API exposed, so external POST clients keep working.

use serde::{Deserialize, Serialize};

/// One progress bar row, as returned by `GET /api/progress`.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ProgressBar {
    pub id: i32,
    pub label: String,
    pub value: i32,
    pub max_value: Option<i32>,
    pub status: Option<String>,
}

/// Body accepted by `POST /api/progress` (upsert by `label`).
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ProgressUpsert {
    pub label: String,
    pub value: i32,
    pub max_value: Option<i32>,
    pub status: Option<String>,
}

/// Percent-filled for rendering, clamped to `[0, 100]`. `max_value` of `None`
/// or `<= 0` yields 0, matching the old client's guard.
pub fn fraction(value: i32, max_value: Option<i32>) -> f64 {
    match max_value {
        Some(max) if max > 0 => ((value as f64 / max as f64) * 100.0).clamp(0.0, 100.0),
        _ => 0.0,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fraction_basics() {
        assert_eq!(fraction(5, Some(10)), 50.0);
        assert_eq!(fraction(0, Some(10)), 0.0);
        assert_eq!(fraction(10, Some(10)), 100.0);
    }

    #[test]
    fn fraction_guards() {
        assert_eq!(fraction(5, None), 0.0);
        assert_eq!(fraction(5, Some(0)), 0.0);
        assert_eq!(fraction(5, Some(-1)), 0.0);
        // Over-full clamps rather than overflowing the bar.
        assert_eq!(fraction(20, Some(10)), 100.0);
    }

    #[test]
    fn progress_bar_round_trips() {
        let bar = ProgressBar {
            id: 1,
            label: "build".to_owned(),
            value: 3,
            max_value: Some(7),
            status: Some("compiling".to_owned()),
        };
        let json = serde_json::to_string(&bar).unwrap();
        let back: ProgressBar = serde_json::from_str(&json).unwrap();
        assert_eq!(back.id, 1);
        assert_eq!(back.max_value, Some(7));
        assert_eq!(back.status.as_deref(), Some("compiling"));
    }

    #[test]
    fn upsert_allows_missing_optionals() {
        let body: ProgressUpsert =
            serde_json::from_str(r#"{"label":"x","value":2}"#).unwrap();
        assert_eq!(body.max_value, None);
        assert_eq!(body.status, None);
    }
}
