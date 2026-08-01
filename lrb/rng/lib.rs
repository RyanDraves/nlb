//! Tiny deterministic xorshift64 RNG shared by the games under `apps/`.
//!
//! Dependency-free on purpose: brm and euc resolve third-party crates from
//! separate crate_universe hubs (`@brm_crates`, `@euc_crates`), so a crate
//! linked by both must not pull external crates — even serde — or the two
//! hubs would supply conflicting types.

/// Advance a raw xorshift64 state and return the new value.
///
/// The free-function form exists so callers that persist the state as a plain
/// `u64` (brm serializes it inside `GameState`) can use it without wrapping.
pub fn next_u64(state: &mut u64) -> u64 {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    *state
}

/// Value in `[0, 1)` from the high bits — bit-identical to the historical
/// `brm_shared::rng_f32` sequence.
pub fn next_f32(state: &mut u64) -> f32 {
    ((next_u64(state) >> 40) as f32) / (1u64 << 24) as f32
}

/// Seedable RNG for callers that don't need to persist the raw state.
#[derive(Clone, Debug)]
pub struct Rng {
    state: u64,
}

impl Rng {
    pub fn from_seed(seed: u64) -> Self {
        // xorshift is stuck at zero forever; remap the one degenerate seed.
        Self {
            state: if seed == 0 { 0x9E37_79B9_7F4A_7C15 } else { seed },
        }
    }

    pub fn next_u64(&mut self) -> u64 {
        next_u64(&mut self.state)
    }

    pub fn next_f32(&mut self) -> f32 {
        next_f32(&mut self.state)
    }

    /// Integer in `[0, n)`. Panics if `n == 0`. Modulo bias is negligible for
    /// the small `n` (deck sizes, jitter windows) these games use.
    pub fn gen_range(&mut self, n: usize) -> usize {
        assert!(n > 0, "gen_range(0)");
        (self.next_u64() % n as u64) as usize
    }

    /// Fisher-Yates shuffle.
    pub fn shuffle<T>(&mut self, xs: &mut [T]) {
        for i in (1..xs.len()).rev() {
            let j = self.gen_range(i + 1);
            xs.swap(i, j);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn deterministic_for_same_seed() {
        let mut a = Rng::from_seed(42);
        let mut b = Rng::from_seed(42);
        for _ in 0..100 {
            assert_eq!(a.next_u64(), b.next_u64());
        }
    }

    #[test]
    fn zero_seed_is_not_stuck() {
        let mut r = Rng::from_seed(0);
        assert_ne!(r.next_u64(), 0);
        assert_ne!(r.next_u64(), r.next_u64());
    }

    #[test]
    fn struct_matches_free_functions() {
        let mut r = Rng::from_seed(7);
        let mut state = 7u64;
        for _ in 0..10 {
            assert_eq!(r.next_u64(), next_u64(&mut state));
        }
    }

    #[test]
    fn f32_in_unit_interval() {
        let mut state = 1u64;
        for _ in 0..1000 {
            let x = next_f32(&mut state);
            assert!((0.0..1.0).contains(&x));
        }
    }

    #[test]
    fn gen_range_in_bounds() {
        let mut r = Rng::from_seed(3);
        for n in 1..50 {
            for _ in 0..100 {
                assert!(r.gen_range(n) < n);
            }
        }
    }

    #[test]
    fn shuffle_is_permutation() {
        let mut r = Rng::from_seed(9);
        let mut xs: Vec<u32> = (0..24).collect();
        r.shuffle(&mut xs);
        let mut sorted = xs.clone();
        sorted.sort();
        assert_eq!(sorted, (0..24).collect::<Vec<u32>>());
        assert_ne!(xs, sorted, "24-element shuffle should not be identity");
    }
}
