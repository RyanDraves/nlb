//! The tile grid.

use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, PartialEq, Eq, Debug, Serialize, Deserialize)]
pub enum Tile {
    Empty,
    /// Indestructible pillar / border.
    Wall,
    /// Destructible block.
    Block,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Map {
    pub w: i32,
    pub h: i32,
    pub tiles: Vec<Tile>,
}

impl Map {
    fn idx(&self, x: i32, y: i32) -> usize {
        (y * self.w + x) as usize
    }

    /// Tile at `(x, y)`; out-of-bounds reads as an indestructible [`Tile::Wall`].
    pub fn get(&self, x: i32, y: i32) -> Tile {
        if x < 0 || y < 0 || x >= self.w || y >= self.h {
            Tile::Wall
        } else {
            self.tiles[self.idx(x, y)]
        }
    }

    pub fn set(&mut self, x: i32, y: i32, t: Tile) {
        if x >= 0 && y >= 0 && x < self.w && y < self.h {
            let i = self.idx(x, y);
            self.tiles[i] = t;
        }
    }
}
