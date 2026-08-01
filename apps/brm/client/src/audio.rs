//! Sound effects + looping music, driven by diffing successive snapshots (the
//! server sends state, not events, so we infer "a bomb was placed", "someone
//! died", "a player readied up", etc. from what changed since the last sim tick).
//!
//! Sounds are synthesized by `assets/gen_sfx.py` and embedded with
//! `include_bytes!`. Browsers block audio until a user gesture, so music only
//! starts once a round begins (which is always after the player has readied
//! up — a real gesture).

use std::collections::HashMap;

use brm_shared::*;
use macroquad::audio::{load_sound_from_bytes, play_sound, stop_sound, PlaySoundParams, Sound};

pub struct Audio {
    place: Sound,
    explode: Sound,
    pickup: Sound,
    death: Sound,
    beep: Sound,
    go: Sound,
    win: Sound,
    ready: Sound,
    unready: Sound,
    music: Sound,

    muted: bool,
    /// Whether music should currently be playing (true during a round, false in
    /// the lobby). Kept separate from `muted` so unmuting resumes correctly.
    music_playing: bool,
    /// Last sim tick we processed, so we diff once per tick (not per frame).
    last_tick: u64,
    /// Whether we've seen any snapshot yet (don't fire sounds for the initial
    /// state we connect into).
    started: bool,

    prev_alive: HashMap<PlayerId, bool>,
    prev_ready: HashMap<PlayerId, bool>,
    prev_powerups: HashMap<PlayerId, u32>,
    prev_phase: Phase,
    prev_count: i32,
}

impl Audio {
    pub async fn load() -> Audio {
        async fn snd(bytes: &[u8]) -> Sound {
            load_sound_from_bytes(bytes).await.expect("decode embedded wav")
        }
        Audio {
            place: snd(include_bytes!("../../assets/sfx/place.wav")).await,
            explode: snd(include_bytes!("../../assets/sfx/explode.wav")).await,
            pickup: snd(include_bytes!("../../assets/sfx/pickup.wav")).await,
            death: snd(include_bytes!("../../assets/sfx/death.wav")).await,
            beep: snd(include_bytes!("../../assets/sfx/beep.wav")).await,
            go: snd(include_bytes!("../../assets/sfx/go.wav")).await,
            win: snd(include_bytes!("../../assets/sfx/win.wav")).await,
            ready: snd(include_bytes!("../../assets/sfx/ready.wav")).await,
            unready: snd(include_bytes!("../../assets/sfx/unready.wav")).await,
            music: snd(include_bytes!("../../assets/sfx/music.wav")).await,
            muted: false,
            music_playing: false,
            last_tick: u64::MAX,
            started: false,
            prev_alive: HashMap::new(),
            prev_ready: HashMap::new(),
            prev_powerups: HashMap::new(),
            prev_phase: Phase::Lobby,
            prev_count: 0,
        }
    }

    pub fn muted(&self) -> bool {
        self.muted
    }

    /// Toggle all audio. Stops the music immediately when muting, and resumes it
    /// when unmuting if a round is in progress.
    pub fn toggle_mute(&mut self) {
        self.muted = !self.muted;
        if self.muted {
            stop_sound(&self.music);
        } else if self.music_playing {
            self.start_music();
        }
    }

    fn sfx(&self, s: &Sound, volume: f32) {
        if !self.muted {
            play_sound(s, PlaySoundParams { looped: false, volume });
        }
    }

    fn start_music(&self) {
        play_sound(&self.music, PlaySoundParams { looped: true, volume: 0.35 });
    }

    /// Inspect the latest snapshot and play whatever changed since the last tick.
    pub fn update(&mut self, latest: &Option<GameState>) {
        let Some(gs) = latest else { return };
        if gs.tick == self.last_tick {
            return; // already handled this sim tick
        }
        let first = !self.started;
        self.last_tick = gs.tick;
        self.started = true;

        // Music runs through a whole round and stops back in the lobby. The
        // first start is always past a user gesture (you readied up to begin).
        let want_music = gs.phase != Phase::Lobby;
        if want_music && !self.music_playing {
            self.music_playing = true;
            if !self.muted {
                self.start_music();
            }
        } else if !want_music && self.music_playing {
            self.music_playing = false;
            stop_sound(&self.music);
        }

        let mut alive = HashMap::new();
        let mut ready = HashMap::new();
        let mut powerups = HashMap::new();
        for p in &gs.players {
            alive.insert(p.id, p.alive);
            ready.insert(p.id, p.ready);
            powerups.insert(p.id, p.powerup_counts().iter().map(|&c| c as u32).sum());
        }

        if !first && gs.phase == Phase::Playing {
            // A freshly placed bomb still has nearly its full fuse; a fresh
            // explosion nearly its full ttl. Both are robust against bombs that
            // slide or chain (whose positions/counts change without a new event).
            if gs.bombs.iter().any(|b| b.fuse > BOMB_FUSE - 0.06) {
                self.sfx(&self.place, 0.5);
            }
            if gs.explosions.iter().any(|e| e.ttl > EXPLOSION_TTL - 0.06) {
                self.sfx(&self.explode, 0.7);
            }
            if powerups
                .iter()
                .any(|(id, &c)| c > *self.prev_powerups.get(id).unwrap_or(&0))
            {
                self.sfx(&self.pickup, 0.5);
            }
            if alive
                .iter()
                .any(|(id, &a)| !a && *self.prev_alive.get(id).unwrap_or(&true))
            {
                self.sfx(&self.death, 0.6);
            }
        }

        // Lobby ready toggles. Gated to staying within the lobby so the bulk
        // ready-reset on returning from a round doesn't fire a burst of blips.
        if !first && gs.phase == Phase::Lobby && self.prev_phase == Phase::Lobby {
            let became_ready = ready
                .iter()
                .any(|(id, &r)| r && !self.prev_ready.get(id).copied().unwrap_or(false));
            let became_unready = ready
                .iter()
                .any(|(id, &r)| !r && self.prev_ready.get(id).copied().unwrap_or(false));
            if became_ready {
                self.sfx(&self.ready, 0.5);
            }
            if became_unready {
                self.sfx(&self.unready, 0.45);
            }
        }

        // Countdown beeps (3-2-1), reset between countdowns so each one chimes.
        if gs.phase == Phase::Countdown {
            let n = gs.phase_timer.ceil().max(0.0) as i32;
            if !first && n != self.prev_count && n >= 1 {
                self.sfx(&self.beep, 0.5);
            }
            self.prev_count = n;
        } else {
            self.prev_count = 0;
        }

        // Phase transitions: "go" on round start, fanfare on a win (a solo loss
        // has no winner and already played the death sound).
        if !first && gs.phase != self.prev_phase {
            match gs.phase {
                Phase::Playing if self.prev_phase == Phase::Countdown => self.sfx(&self.go, 0.5),
                Phase::RoundOver if gs.winner.is_some() => self.sfx(&self.win, 0.6),
                _ => {}
            }
        }

        self.prev_alive = alive;
        self.prev_ready = ready;
        self.prev_powerups = powerups;
        self.prev_phase = gs.phase;
    }
}
