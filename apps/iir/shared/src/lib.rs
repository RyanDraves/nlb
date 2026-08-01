//! Wire types shared by the iir server and its Leptos wasm client. The
//! `is_raining` classifier is pure so it can be unit-tested without any HTTP.

use serde::{Deserialize, Serialize};

/// The subset of the OpenWeatherMap "current weather" response we parse.
#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub struct OwmResponse {
    #[serde(default)]
    pub weather: Vec<OwmCondition>,
}

/// One reported weather condition (there can be several, e.g. "rain" + "mist").
#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub struct OwmCondition {
    #[serde(default)]
    pub main: String,
    #[serde(default)]
    pub description: String,
}

/// Our `/api/weather` success payload.
#[derive(Debug, Clone, Copy, Deserialize, Serialize)]
pub struct WeatherStatus {
    pub raining: bool,
}

/// Our `/api/weather` error payload (also returned on non-2xx).
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ErrorBody {
    pub error: String,
}

/// True if any reported condition's `main` or `description` mentions rain.
/// Mirrors the check in the old `apps/iir/app/api/weather/route.ts`.
pub fn is_raining(resp: &OwmResponse) -> bool {
    resp.weather.iter().any(|c| {
        c.main.to_lowercase().contains("rain") || c.description.to_lowercase().contains("rain")
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cond(main: &str, desc: &str) -> OwmCondition {
        OwmCondition {
            main: main.to_owned(),
            description: desc.to_owned(),
        }
    }

    #[test]
    fn detects_rain_in_main() {
        let r = OwmResponse {
            weather: vec![cond("Rain", "moderate rain")],
        };
        assert!(is_raining(&r));
    }

    #[test]
    fn detects_rain_in_description_only() {
        let r = OwmResponse {
            weather: vec![cond("Drizzle", "light intensity drizzle rain")],
        };
        assert!(is_raining(&r));
    }

    #[test]
    fn clear_is_not_raining() {
        let r = OwmResponse {
            weather: vec![cond("Clear", "clear sky")],
        };
        assert!(!is_raining(&r));
    }

    #[test]
    fn empty_is_not_raining() {
        assert!(!is_raining(&OwmResponse::default()));
    }

    #[test]
    fn parses_owm_json_subset() {
        let json = r#"{"coord":{"lon":-105.2,"lat":40.0},
            "weather":[{"id":500,"main":"Rain","description":"light rain","icon":"10d"}],
            "base":"stations","main":{"temp":12.3},"name":"Boulder"}"#;
        let resp: OwmResponse = serde_json::from_str(json).unwrap();
        assert!(is_raining(&resp));
    }

    #[test]
    fn status_round_trips() {
        let s = WeatherStatus { raining: true };
        let json = serde_json::to_string(&s).unwrap();
        assert_eq!(json, r#"{"raining":true}"#);
    }
}
