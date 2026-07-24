#!/usr/bin/env python3
"""Generate the PWA / home-screen icons: a felt-green tile with a fanned pair
of cards. Pure standard library (hand-rolled PNG encoder, same pattern as
apps/brm/assets/gen_powerups.py) so it runs anywhere with no pip installs.

Run from this directory:

    python3 gen_icons.py    # writes ../web/icon-{180,192,512}.png

Renders one 1024px master with rotated-rect coverage tests, then
box-downsamples to each output size (the downsample is the anti-aliasing).
"""

import math
import struct
import zlib

M = 1024  # master size

FELT = (28, 92, 57)
FELT_DARK = (17, 55, 34)
CARD = (253, 252, 247)
CARD_EDGE = (185, 180, 166)
RED = (192, 39, 45)
BACK = (53, 82, 142)

buf = bytearray(M * M * 4)


def setpx(x, y, c):
    i = (y * M + x) * 4
    buf[i] = c[0]
    buf[i + 1] = c[1]
    buf[i + 2] = c[2]
    buf[i + 3] = 255


def rot(x, y, cx, cy, deg):
    """Point (x,y) in the local frame of a rect centered at (cx,cy), rotated deg."""
    th = math.radians(deg)
    dx, dy = x - cx, y - cy
    return (
        dx * math.cos(th) + dy * math.sin(th),
        -dx * math.sin(th) + dy * math.cos(th),
    )


def in_round_rect(lx, ly, hw, hh, r):
    ax, ay = abs(lx), abs(ly)
    if ax > hw or ay > hh:
        return False
    if ax <= hw - r or ay <= hh - r:
        return True
    return (ax - (hw - r)) ** 2 + (ay - (hh - r)) ** 2 <= r * r


def in_diamond(lx, ly, w, h):
    return abs(lx) / w + abs(ly) / h <= 1.0


# Card geometry (master pixels).
HW, HH, R = 210, 300, 40  # half-width, half-height, corner radius
BORDER = 22


def paint():
    for y in range(M):
        for x in range(M):
            # Felt: radial falloff toward the corners.
            d = math.hypot(x - M / 2, y - M * 0.42) / (M * 0.75)
            d = min(d, 1.0)
            c = tuple(int(FELT[i] + (FELT_DARK[i] - FELT[i]) * d) for i in range(3))

            # Back card (blue, tilted left) behind the face card.
            lx, ly = rot(x, y, M * 0.40, M * 0.46, -14)
            if in_round_rect(lx, ly, HW, HH, R):
                inner = in_round_rect(lx, ly, HW - BORDER, HH - BORDER, R // 2)
                c = BACK if inner else CARD
                # Simple lattice on the card back.
                if inner and (int(lx + ly) % 56 < 7 or int(lx - ly) % 56 < 7):
                    c = (77, 108, 170)

            # Face card (white, tilted right) with a big red diamond.
            lx, ly = rot(x, y, M * 0.58, M * 0.54, 11)
            if in_round_rect(lx, ly, HW, HH, R):
                c = CARD
                if not in_round_rect(lx, ly, HW - 6, HH - 6, R):
                    c = CARD_EDGE
                if in_diamond(lx, ly, 120, 170):
                    c = RED

            setpx(x, y, c)


def downsample(size):
    out = bytearray(size * size * 4)
    step = M / size
    for y in range(size):
        y0, y1 = int(y * step), max(int((y + 1) * step), int(y * step) + 1)
        for x in range(size):
            x0, x1 = int(x * step), max(int((x + 1) * step), int(x * step) + 1)
            r = g = b = n = 0
            for sy in range(y0, y1):
                base = (sy * M + x0) * 4
                for sx in range(x0, x1):
                    i = base + (sx - x0) * 4
                    r += buf[i]
                    g += buf[i + 1]
                    b += buf[i + 2]
                    n += 1
            i = (y * size + x) * 4
            out[i] = r // n
            out[i + 1] = g // n
            out[i + 2] = b // n
            out[i + 3] = 255
    return out


def write_png(path, size, pixels):
    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter: none
        raw += pixels[y * size * 4 : (y + 1) * size * 4]
    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    out += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(out)


paint()
for size in (512, 192, 180):
    write_png(f"../web/icon-{size}.png", size, downsample(size))
    print(f"wrote ../web/icon-{size}.png")
