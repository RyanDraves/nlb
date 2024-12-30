#![no_std]

use lazy_static::lazy_static;
use spin::Mutex;
use wasm_bindgen::prelude::*;

#[macro_use]
mod utils;

extern crate wee_alloc;

extern crate web_sys;
use web_sys::console;

const WIDTH: u32 = 256;
const HEIGHT: u32 = 128;

lazy_static! {
    static ref CELL_BUFFER_0: Mutex<[Cell; (WIDTH * HEIGHT) as usize]> =
        Mutex::new([Cell::Dead; (WIDTH * HEIGHT) as usize]);
    static ref CELL_BUFFER_1: Mutex<[Cell; (WIDTH * HEIGHT) as usize]> =
        Mutex::new([Cell::Dead; (WIDTH * HEIGHT) as usize]);
    static ref UNIVERSE: Mutex<Universe> = Mutex::new(Universe {
        cells: &CELL_BUFFER_0,
        buffer: 0,
    });
}

#[wasm_bindgen]
#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Cell {
    Dead = 0,
    Alive = 1,
}

impl Cell {
    fn toggle(&mut self) {
        *self = match *self {
            Cell::Dead => Cell::Alive,
            Cell::Alive => Cell::Dead,
        };
    }
}

#[wasm_bindgen]
pub struct Universe {
    cells: &'static Mutex<[Cell; (WIDTH * HEIGHT) as usize]>,
    buffer: u8,
}

impl Universe {
    fn get_index(&self, row: u32, column: u32) -> usize {
        (row * WIDTH + column) as usize
    }

    fn live_neighbor_count(
        &self,
        row: u32,
        column: u32,
        cells: &spin::MutexGuard<[Cell; (WIDTH * HEIGHT) as usize]>,
    ) -> u8 {
        let mut count = 0;

        let north = if row == 0 { HEIGHT - 1 } else { row - 1 };

        let south = if row == HEIGHT - 1 { 0 } else { row + 1 };

        let west = if column == 0 { WIDTH - 1 } else { column - 1 };

        let east = if column == WIDTH - 1 { 0 } else { column + 1 };

        let nw = self.get_index(north, west);
        count += cells[nw] as u8;

        let n = self.get_index(north, column);
        count += cells[n] as u8;

        let ne = self.get_index(north, east);
        count += cells[ne] as u8;

        let w = self.get_index(row, west);
        count += cells[w] as u8;

        let e = self.get_index(row, east);
        count += cells[e] as u8;

        let sw = self.get_index(south, west);
        count += cells[sw] as u8;

        let s = self.get_index(south, column);
        count += cells[s] as u8;

        let se = self.get_index(south, east);
        count += cells[se] as u8;

        count
    }

    pub fn set_cells(&mut self, cells: &[(u32, u32)]) {
        let mut self_cells = self.cells.lock();
        for (row, col) in cells.iter() {
            let idx = self.get_index(*row, *col);
            self_cells[idx] = Cell::Alive;
        }
    }
}

#[wasm_bindgen]
impl Universe {
    pub fn tick(&mut self) {
        let next_mutex: &'static Mutex<[Cell; (WIDTH * HEIGHT) as usize]> = match self.buffer {
            0 => &CELL_BUFFER_1,
            _ => &CELL_BUFFER_0,
        };

        self.buffer = match self.buffer {
            0 => 1,
            _ => 0,
        };

        let mut next = next_mutex.lock();

        let cells = self.cells.lock();

        for row in 0..HEIGHT {
            for col in 0..WIDTH {
                let idx = self.get_index(row, col);
                let cell = cells[idx];
                let live_neighbors = self.live_neighbor_count(row, col, &cells);

                // log!(
                //     "cell[{}, {}] is initially {:?} and has {} live neighbors",
                //     row,
                //     col,
                //     cell,
                //     live_neighbors
                // );

                let next_cell = match (cell, live_neighbors) {
                    // Rule 1: Any live cell with fewer than two live neighbours
                    // dies, as if caused by underpopulation.
                    (Cell::Alive, x) if x < 2 => Cell::Dead,
                    // Rule 2: Any live cell with two or three live neighbours
                    // lives on to the next generation.
                    (Cell::Alive, 2) | (Cell::Alive, 3) => Cell::Alive,
                    // Rule 3: Any live cell with more than three live
                    // neighbours dies, as if by overpopulation.
                    (Cell::Alive, x) if x > 3 => Cell::Dead,
                    // Rule 4: Any dead cell with exactly three live neighbours
                    // becomes a live cell, as if by reproduction.
                    (Cell::Dead, 3) => Cell::Alive,
                    // All other cells remain in the same state.
                    (otherwise, _) => otherwise,
                };

                // log!("    it becomes {:?}", next_cell);

                next[idx] = next_cell;
            }
        }

        self.cells = next_mutex;
    }

    pub fn initialize(&self) {
        let mut cells = self.cells.lock();
        for (i, cell) in cells.iter_mut().enumerate() {
            *cell = if i % 2 == 0 || i % 7 == 0 {
                Cell::Alive
            } else {
                Cell::Dead
            }
        }
    }

    pub fn get_cells(&self) -> *const Cell {
        self.cells.lock().as_ptr()
    }

    pub fn toggle_cell(&mut self, row: u32, column: u32) {
        let idx = self.get_index(row, column);
        self.cells.lock()[idx].toggle();
    }
}

pub struct Timer<'a> {
    name: &'a str,
}

impl<'a> Timer<'a> {
    pub fn new(name: &'a str) -> Timer<'a> {
        console::time_with_label(name);
        Timer { name }
    }
}

impl<'a> Drop for Timer<'a> {
    fn drop(&mut self) {
        console::time_end_with_label(self.name);
    }
}

#[wasm_bindgen]
extern "C" {
    fn alert(s: &str);
}

#[wasm_bindgen]
pub fn greet(msg: &str) {
    alert(msg);
}

#[wasm_bindgen]
pub fn initialize() {
    utils::set_panic_hook();
}

#[wasm_bindgen]
pub fn width() -> u32 {
    WIDTH
}

#[wasm_bindgen]
pub fn height() -> u32 {
    HEIGHT
}

#[wasm_bindgen]
pub fn create_universe() {
    let universe = UNIVERSE.lock();
    universe.initialize();
}

#[wasm_bindgen]
pub fn tick() {
    let mut universe = UNIVERSE.lock();
    universe.tick();
}

#[wasm_bindgen]
pub fn get_cells() -> *const Cell {
    let universe = UNIVERSE.lock();
    universe.get_cells()
}

#[wasm_bindgen]
pub fn toggle_cell(row: u32, column: u32) {
    let mut universe = UNIVERSE.lock();
    universe.toggle_cell(row, column);
}
