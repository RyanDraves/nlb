// Mission descriptions for the satellite visualization.

export interface Mission {
  /** NORAD catalog id; must match a key in tles.json. */
  noradId: string;
  /** Mission / satellite name shown as the tooltip heading. */
  name: string;
  /** Who operates the satellite (optional). */
  operator?: string;
  /** What Ryan worked on for this mission. */
  role: string;
  /** Orbit regime — drives how the orbit is drawn/labeled. */
  orbit: "LEO" | "GEO";
  /** Launch year, e.g. "2023" (optional). */
  launched?: string;
  /** Current status — "deorbited" renders the orbit in a dimmed/dashed style. */
  status: "active" | "deorbited";
  /** 1–3 sentence description shown in the tooltip body. */
  blurb: string;
}

/**
 * Split a blurb into an optional reference URL and the remaining prose, so the
 * UI can render the URL as a clickable link rather than raw text.
 */
export function splitBlurb(blurb: string): { url?: string; text: string } {
  const match = blurb.match(/(https?:\/\/\S+)/);
  if (!match) return { text: blurb.trim() };
  return { url: match[1], text: blurb.replace(match[1], "").trim() };
}

export const missions: Record<string, Mission> = {
  "55123": {
    noradId: "55123",
    name: "MARIO",
    role: "Radio and command handling",
    orbit: "LEO",
    launched: "2022-12-26",
    status: "deorbited",
    blurb: "https://exploration.engin.umich.edu/mario-launched-deployed-and-operational/",
  },
  "56371": {
    noradId: "56371",
    name: "Arcturus",
    role: "Payload testing",
    orbit: "GEO",
    launched: "2023-05-01",
    status: "active",
    blurb: "https://www.astranis.com/blog/first-astranis-satellite-successfully-deployed-to-geo-beams-first-signals-down-to-alaska-257ba",
  },
  "62454": {
    noradId: "62454",
    name: "UtilitySat",
    role: "RFFE firmware and payload testing",
    orbit: "GEO",
    launched: "2024-12-29",
    status: "active",
    blurb: "https://www.satcat.com/sats/62454 Just one more rework it's gonna work this time...",
  },
  "62455": {
    noradId: "62455",
    name: "Nuview Alpha",
    role: "RFFE firmware and payload testing",
    orbit: "GEO",
    launched: "2024-12-29",
    status: "active",
    blurb: "https://www.satcat.com/sats/62455",
  },
  "62456": {
    noradId: "62456",
    name: "Agila",
    role: "RFFE firmware and payload testing",
    orbit: "GEO",
    launched: "2024-12-29",
    status: "active",
    blurb: "https://www.satcat.com/sats/62456",
  },
  "62457": {
    noradId: "62457",
    name: "Nuview Bravo",
    role: "RFFE firmware and payload testing",
    orbit: "GEO",
    launched: "2024-12-29",
    status: "active",
    blurb: "https://www.satcat.com/sats/62457",
  },
};
