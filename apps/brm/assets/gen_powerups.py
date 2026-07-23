#!/usr/bin/env python3
"""Generate `powerups.png`: a 192x32 horizontal strip of six 32x32 power-up
icons, in `PowerKind::ALL` order (ExtraBomb, Range, Speed, Kick, Pierce, Shield).

Pure standard library (hand-rolled PNG encoder) so it runs anywhere with no
pip installs. Run from this directory:

    python3 gen_powerups.py            # writes powerups.png
    python3 gen_powerups.py --preview  # also writes /tmp/powerups_preview.png (8x)

The client embeds the PNG via include_bytes! and scales it with Nearest
filtering, so the art is intentionally crisp/blocky pixel art.
"""

import math
import struct
import sys
import zlib

W = H = 32  # one cell
N = 6
SW = W * N  # sheet width

# RGBA sheet, transparent background.
buf = bytearray(SW * H * 4)


def _i(x, y):
    return (y * SW + x) * 4


def setpx(x, y, c):
    if 0 <= x < SW and 0 <= y < H:
        i = _i(x, y)
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]
        buf[i + 3] = 255


def rect(ox, x0, y0, x1, y1, c):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            setpx(ox + x, y, c)


def disc(ox, cx, cy, r, c):
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                setpx(ox + x, y, c)


def ring(ox, cx, cy, r, th, c):
    ri = r - th
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if ri * ri <= d2 <= r * r:
                setpx(ox + x, y, c)


def line(ox, x0, y0, x1, y1, c):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        setpx(ox + x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def thick_line(ox, x0, y0, x1, y1, r0, r1, c):
    """A tapered capsule from (x0,y0) radius r0 to (x1,y1) radius r1."""
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
    for s in range(steps + 1):
        t = s / steps
        cx = x0 + (x1 - x0) * t
        cy = y0 + (y1 - y0) * t
        disc(ox, cx, cy, r0 + (r1 - r0) * t, c)


def fill_poly(ox, pts, c):
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        for i in range(len(pts)):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % len(pts)]
            if (ay <= y < by) or (by <= y < ay):
                xs.append(ax + (bx - ax) * (y - ay) / (by - ay))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            for x in range(int(round(xs[k])), int(round(xs[k + 1])) + 1):
                setpx(ox + x, y, c)


def stroke_poly(ox, pts, c):
    for i in range(len(pts)):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % len(pts)]
        line(ox, ax, ay, bx, by, c)


# --- palette ---------------------------------------------------------------
OUT = (18, 18, 26)
BOMB = (36, 36, 47)
BOMB_HI = (200, 210, 228)
SPARK = (255, 216, 120)
FL_O = (240, 110, 30)
FL_M = (255, 182, 48)
FL_C = (255, 242, 188)
BOOT = (44, 192, 182)
BOOT_D = (22, 120, 114)
SOLE = (18, 92, 88)
WING = (238, 246, 250)
BAT = (172, 124, 68)
BAT_D = (120, 84, 44)
CRATE = (176, 124, 72)
CRATE_HI = (208, 158, 100)
CRATE_LN = (86, 56, 30)
WHITE = (245, 245, 250)
GREEN = (96, 202, 116)
PURPLE = (178, 114, 230)
RING = (90, 202, 242)
SHIELD = (178, 184, 196)
SHIELD_D = (120, 126, 140)


def ball(ox, cx, cy, r, body):
    """A bomb: outlined dark sphere with a highlight and a little fuse spark."""
    disc(ox, cx, cy, r, OUT)
    disc(ox, cx, cy, r - 1, body)
    disc(ox, cx - r * 0.32, cy - r * 0.34, max(1.0, r * 0.26), BOMB_HI)
    # fuse + spark out the top
    line(ox, cx, cy - r, cx + 1, cy - r - 2, OUT)
    disc(ox, cx + 1, cy - r - 3, 1.6, SPARK)


def plus_badge(ox, cx, cy, r, disc_c):
    disc(ox, cx, cy, r + 1, OUT)
    disc(ox, cx, cy, r, disc_c)
    rect(ox, cx - r + 1.5, cy - 1, cx + r - 1.5, cy + 1, WHITE)
    rect(ox, cx - 1, cy - r + 1.5, cx + 1, cy + r - 1.5, WHITE)


# --- icons -----------------------------------------------------------------
def extra_bomb(ox):
    ball(ox, 9, 12, 4, BOMB)  # small, back
    ball(ox, 21, 12, 6, BOMB)  # medium, upper right
    ball(ox, 12, 20, 8, BOMB)  # big, front
    plus_badge(ox, 25, 25, 5, GREEN)


def range_icon(ox):
    # explosion cross + layered core
    rect(ox, 4, 13, 27, 18, FL_O)
    rect(ox, 13, 4, 18, 27, FL_O)
    rect(ox, 7, 14, 24, 17, FL_M)
    rect(ox, 14, 7, 17, 24, FL_M)
    disc(ox, 16, 16, 9, FL_O)
    disc(ox, 16, 16, 6, FL_M)
    disc(ox, 16, 16, 3, FL_C)
    # spiky tips
    for (tx, ty) in [(16, 3), (16, 28), (3, 16), (28, 16)]:
        disc(ox, tx, ty, 1.6, FL_M)


def speed(ox):
    # A wing of three feathers sweeping up-and-back off the ankle (behind the
    # boot). Tips climb left; bases stack down the boot's heel.
    for wing in (
        [(16, 9), (16, 12), (4, 4)],
        [(16, 12), (16, 15), (5, 9)],
        [(16, 15), (16, 18), (8, 14)],
    ):
        fill_poly(ox, wing, WING)
        stroke_poly(ox, wing, OUT)
    # Boot: shaft + foot with a toe and a small heel, facing right.
    boot = [(16, 7), (22, 7), (22, 19), (28, 19), (28, 25), (17, 25), (16, 22)]
    fill_poly(ox, boot, BOOT)
    stroke_poly(ox, boot, OUT)
    rect(ox, 17, 24, 27, 25, SOLE)  # sole
    line(ox, 19, 10, 21, 10, BOOT_D)  # laces
    line(ox, 19, 13, 21, 13, BOOT_D)


def kick(ox):
    ball(ox, 23, 22, 7, BOMB)  # bomb being hit
    thick_line(ox, 6, 8, 18, 18, 1.2, 4.0, OUT)  # bat outline
    thick_line(ox, 6, 8, 18, 18, 0.4, 2.8, BAT)  # bat body
    disc(ox, 5, 7, 2.4, BAT_D)  # handle knob
    # impact flash at contact
    disc(ox, 19, 18, 2.0, WHITE)
    for (dx, dy) in [(3, 0), (-3, 0), (0, 3), (0, -3), (2, 2), (-2, -2)]:
        line(ox, 19, 18, 19 + dx, 18 + dy, WHITE)


def pierce(ox):
    rect(ox, 6, 6, 25, 25, CRATE)
    rect(ox, 6, 6, 25, 8, CRATE_HI)
    line(ox, 6, 6, 25, 25, CRATE_LN)
    line(ox, 25, 6, 6, 25, CRATE_LN)
    stroke_poly(ox, [(6, 6), (25, 6), (25, 25), (6, 25)], OUT)
    plus_badge(ox, 25, 25, 5, PURPLE)


def shield(ox):
    ring(ox, 16, 15, 13, 3, RING)
    sh = [(10, 9), (22, 9), (22, 15), (16, 24), (10, 15)]
    fill_poly(ox, sh, SHIELD)
    stroke_poly(ox, sh, OUT)
    line(ox, 16, 10, 16, 22, SHIELD_D)  # heraldic divider
    line(ox, 11, 12, 21, 12, SHIELD_D)


ICONS = [extra_bomb, range_icon, speed, kick, pierce, shield]
for i, fn in enumerate(ICONS):
    fn(i * W)


# --- PNG encode ------------------------------------------------------------
def write_png(path, width, height, pixels):
    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter: none
        raw += pixels[y * width * 4 : (y + 1) * width * 4]
    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    out += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(out)


write_png("powerups.png", SW, H, buf)
print("wrote powerups.png", SW, "x", H)

if "--preview" in sys.argv:
    scale = 8
    pw, ph = SW * scale, H * scale
    big = bytearray(pw * ph * 4)
    for y in range(ph):
        for x in range(pw):
            si = _i(x // scale, y // scale)
            di = (y * pw + x) * 4
            big[di : di + 4] = buf[si : si + 4]
    write_png("/tmp/powerups_preview.png", pw, ph, big)
    print("wrote /tmp/powerups_preview.png", pw, "x", ph)
