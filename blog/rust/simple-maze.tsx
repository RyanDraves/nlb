"use client";

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

// const Cell = ({ is_wall, is_player, is_goal }: { is_wall: boolean, is_player: boolean, is_goal: boolean }) => {
//     return (
//         <motion.div
//             className={`
//                 ${is_player ? 'bg-triadic' :
//                     is_goal ? 'bg-analogous_800' :
//                         is_wall ? 'bg-complementary' : 'bg-analogous'} border border-analogous2`}
//             whileHover={{ scale: 1.1 }}
//             initial={{ opacity: 0 }}
//             animate={{ opacity: 1 }}
//         >&nbsp;</motion.div>
//     );
// };

// const SimpleMaze = () => {
//     const maze = [
//         [false, false, false, false, false],
//         [false, true, true, true, false],
//         [false, false, false, false, false],
//         [false, true, true, true, false],
//         [false, false, false, false, false],
//     ];

//     const goal_pos = { x: 4, y: 4 };

//     const [player_pos, setPlayerPos] = useState({ x: 0, y: 0 });

//     useEffect(() => {
//         function handleKeyDown(e: KeyboardEvent) {
//             switch (e.key) {
//                 case 'ArrowUp':
//                     setPlayerPos({ x: player_pos.x, y: player_pos.y - 1 });
//                     break;
//                 case 'ArrowDown':
//                     setPlayerPos({ x: player_pos.x, y: player_pos.y + 1 });
//                     break;
//                 case 'ArrowLeft':
//                     setPlayerPos({ x: player_pos.x - 1, y: player_pos.y });
//                     break;
//                 case 'ArrowRight':
//                     setPlayerPos({ x: player_pos.x + 1, y: player_pos.y });
//                     break;
//             }
//         }
//         window.addEventListener('keydown', handleKeyDown);
//         return () => window.removeEventListener('keydown', handleKeyDown);
//     }, [player_pos]);

//     return (
//         <div className="grid grid-cols-5 gap-0">
//             {maze.map((row, i) =>
//                 row.map((cell, j) => (
//                     <Cell key={`${i}-${j}`} is_wall={cell} is_goal={i === goal_pos.y && j === goal_pos.x} is_player={i === player_pos.y && j === player_pos.x} />
//                 ))
//             )}
//         </div>
//     );
// };

// export default SimpleMaze;



// Cell size in pixels (assumes 5x5 grid)
const CELL_SIZE = 120;

interface CellProps {
    isWall: boolean;
    isGoal: boolean;
}

// Basic cell for walls/empty
function Cell({ isWall, isGoal }: CellProps) {
    // Priority: goal color > wall color > empty color
    let bgClass = "bg-analogous border border-analogous2";
    if (isWall) bgClass = "bg-complementary border border-analogous2";
    if (isGoal) bgClass = "bg-analogous_800 border border-analogous2";

    return <div className={bgClass} style={{ width: CELL_SIZE, height: CELL_SIZE }} />;
}
type Direction = "up" | "down" | "left" | "right";

// Rotation angles for the arrow
const directionAngle: Record<Direction, number> = {
    up: 0,
    right: 90,
    down: 180,
    left: -90,
};

export default function SimpleMaze() {
    // Maze: true = wall, false = empty
    const maze = [
        [false, false, false, false, false],
        [false, true, true, true, false],
        [false, false, false, false, false],
        [false, true, true, true, false],
        [false, false, false, false, false],
    ];

    // Goal at bottom-right cell
    const goalPos = { row: 4, col: 4 };

    // Player state
    const [playerPos, setPlayerPos] = useState({ row: 0, col: 0 });
    const [direction, setDirection] = useState<Direction>("right"); // track arrow direction

    // Handle WASD movement
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            let { row, col } = playerPos;
            if (e.key === "w") {
                setDirection("up");
                if (row > 0 && !maze[row - 1][col]) row--;
            }
            if (e.key === "s") {
                setDirection("down");
                if (row < 4 && !maze[row + 1][col]) row++;
            }
            if (e.key === "a") {
                setDirection("left");
                if (col > 0 && !maze[row][col - 1]) col--;
            }
            if (e.key === "d") {
                setDirection("right");
                if (col < 4 && !maze[row][col + 1]) col++;
            }
            setPlayerPos({ row, col });
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [playerPos]);

    return (
        <div
            className="relative"
            style={{
                width: CELL_SIZE * 5,
                height: CELL_SIZE * 5,
            }}
        >
            {/* Maze cells */}
            <div className="grid grid-cols-5 absolute top-0 left-0">
                {maze.map((row, rowIndex) =>
                    row.map((isWall, colIndex) => (
                        <Cell
                            key={`${rowIndex}-${colIndex}`}
                            isWall={isWall}
                            isGoal={rowIndex === goalPos.row && colIndex === goalPos.col}
                        />
                    ))
                )}
            </div>

            {/* Player + Arrow */}
            <motion.div
                style={{ position: "absolute" }}
                animate={{
                    x: playerPos.col * CELL_SIZE,
                    y: playerPos.row * CELL_SIZE,
                }}
                transition={{ type: "spring", stiffness: 120 }}
            >
                {/* Player square */}
                <div
                    className="bg-triadic border border-analogous2"
                    style={{ width: CELL_SIZE, height: CELL_SIZE, position: "relative" }}
                >
                    {/* Arrow (a small triangle) positioned in the center, rotated based on direction */}
                    <motion.div
                        className="absolute left-1/2 top-1/2"
                        style={{
                            width: 0,
                            height: 0,
                            borderLeft: "10px solid transparent",
                            borderRight: "10px solid transparent",
                            borderBottom: `15px solid #FAF089`, // matches 'bg-triadic' color if needed, or override
                            translateX: "-50%",
                            translateY: "-70%", // shift it up so arrow tip is near the edge
                        }}
                        animate={{ rotate: directionAngle[direction] }}
                    />
                </div>
            </motion.div>
        </div>
    );
}
