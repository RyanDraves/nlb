"use client";

import * as wasm from "@nlb/lrb/game_of_life/game_of_life";
import { memory } from "@nlb/lrb/game_of_life/game_of_life_bg.wasm";
import React, { useEffect, useRef, useState } from 'react';
import { usePathname } from 'next/navigation';

const GameOfLife = () => {
    const pathname = usePathname();
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const playButtonRef = useRef<HTMLButtonElement>(null);
    const fpsRef = useRef<HTMLPreElement>(null);
    const animationIdRef = useRef<number | null>(null);
    let lastTimestamp: number | null = null;

    useEffect(() => {
        const TARGET_FPS = 60;
        const FRAME_INTERVAL = 1000 / TARGET_FPS;

        const CELL_SIZE = 5; // px
        const GRID_COLOR = "#CCCCCC";
        const DEAD_COLOR = "#FFFFFF";
        const ALIVE_COLOR = "#000000";

        wasm.initialize();
        wasm.create_universe();
        const width = wasm.width();
        const height = wasm.height();

        const canvas = canvasRef.current;
        if (!canvas) { return; }
        canvas.height = (CELL_SIZE + 1) * height + 1;
        canvas.width = (CELL_SIZE + 1) * width + 1;

        const ctx = canvas.getContext('2d');
        const playButton = playButtonRef.current;
        if (!ctx || !playButton) { return; }

        const renderLoop = (timestamp: number | null) => {
            timestamp = timestamp || 0;
            if (lastTimestamp === null) {
                lastTimestamp = timestamp;
            }
            const delta = timestamp - lastTimestamp;

            if (delta < FRAME_INTERVAL) {
                animationIdRef.current = requestAnimationFrame(renderLoop);
                return;
            }

            FpsMeter.render();

            wasm.tick();

            drawGrid();
            drawCells();

            animationIdRef.current = requestAnimationFrame(renderLoop);
        };

        const isPaused = () => {
            return animationIdRef.current === null;
        };

        const pause = () => {
            if (animationIdRef.current === null) {
                return;
            }
            playButton.textContent = "▶";
            cancelAnimationFrame(animationIdRef.current);
            animationIdRef.current = null;
        };

        const play = () => {
            playButton.textContent = "⏸";
            renderLoop(null);
        };

        const handlePlayPause = () => {
            if (isPaused()) {
                play();
            } else {
                pause();
            }
        }

        playButton.addEventListener("click", handlePlayPause);

        const drawGrid = () => {
            ctx.beginPath();
            ctx.strokeStyle = GRID_COLOR;

            for (let i = 0; i <= width; i++) {
                ctx.moveTo(i * (CELL_SIZE + 1) + 1, 0);
                ctx.lineTo(i * (CELL_SIZE + 1) + 1, (CELL_SIZE + 1) * height + 1);
            }

            for (let j = 0; j <= height; j++) {
                ctx.moveTo(0, j * (CELL_SIZE + 1) + 1);
                ctx.lineTo((CELL_SIZE + 1) * width + 1, j * (CELL_SIZE + 1) + 1);
            }

            ctx.stroke();
        };

        const getIndex = (row: number, column: number) => {
            return row * width + column;
        };

        const drawCells = () => {
            const cellsPtr = wasm.get_cells();
            const cells = new Uint8Array(memory.buffer, cellsPtr, width * height);

            ctx.beginPath();

            ctx.fillStyle = ALIVE_COLOR;
            for (let row = 0; row < height; row++) {
                for (let col = 0; col < width; col++) {
                    const idx = getIndex(row, col);

                    if (cells[idx] === wasm.Cell.Alive) {
                        ctx.fillRect(
                            col * (CELL_SIZE + 1) + 1,
                            row * (CELL_SIZE + 1) + 1,
                            CELL_SIZE,
                            CELL_SIZE
                        );
                    }
                }
            }

            ctx.fillStyle = DEAD_COLOR;
            for (let row = 0; row < height; row++) {
                for (let col = 0; col < width; col++) {
                    const idx = getIndex(row, col);

                    if (cells[idx] === wasm.Cell.Dead) {
                        ctx.fillRect(
                            col * (CELL_SIZE + 1) + 1,
                            row * (CELL_SIZE + 1) + 1,
                            CELL_SIZE,
                            CELL_SIZE
                        );
                    }
                }
            }

            ctx.stroke();
        };

        const handleCanvasClick = (event: MouseEvent) => {
            const boundingRect = canvas.getBoundingClientRect();

            const scaleX = canvas.width / boundingRect.width;
            const scaleY = canvas.height / boundingRect.height;

            const canvasLeft = (event.clientX - boundingRect.left) * scaleX;
            const canvasTop = (event.clientY - boundingRect.top) * scaleY;

            const row = Math.min(Math.floor(canvasTop / (CELL_SIZE + 1)), height - 1);
            const col = Math.min(Math.floor(canvasLeft / (CELL_SIZE + 1)), width - 1);

            wasm.toggle_cell(row, col);

            drawCells();
        }

        canvas.addEventListener("click", handleCanvasClick);

        const FpsMeter = new class {
            fps: HTMLPreElement | null;
            frames: number[];
            lastFrameTimeStamp: number

            constructor() {
                this.fps = fpsRef.current;
                this.frames = [];
                this.lastFrameTimeStamp = performance.now();
            }

            render() {
                const now = performance.now();
                const delta = now - this.lastFrameTimeStamp;
                this.lastFrameTimeStamp = now;
                const fps = 1 / delta * 1000;

                this.frames.push(fps);
                if (this.frames.length > 100) {
                    this.frames.shift();
                }

                let min = Infinity;
                let max = -Infinity;
                let sum = 0;
                for (let i = 0; i < this.frames.length; i++) {
                    sum += this.frames[i];
                    min = Math.min(this.frames[i], min);
                    max = Math.max(this.frames[i], max);
                }
                let mean = sum / this.frames.length;

                if (!this.fps) {
                    return;
                }
                this.fps.textContent = `
Frames per Second:
latest = ${Math.round(fps)}
avg of last 100 = ${Math.round(mean)}
min of last 100 = ${Math.round(min)}
max of last 100 = ${Math.round(max)}
`.trim();
            }
        };

        drawGrid();
        drawCells();

        // Cleanup
        return () => {
            playButton.removeEventListener("click", handlePlayPause);
            canvas.removeEventListener("click", handleCanvasClick);
            cancelAnimationFrame(animationIdRef.current!);
            animationIdRef.current = null;
        };
    },
        // Re-run the effect when the pathname changes
        [pathname]);

    return (
        <div className="max-w-2xl mx-auto flex flex-col items-center overflow-x-auto">
            <button ref={playButtonRef} id="play-pause">▶</button>
            <canvas ref={canvasRef} id="game-of-life-canvas"></canvas>
            <pre ref={fpsRef} id="fps"></pre>
        </div>
    );
};

export default GameOfLife;
