#!/usr/bin/env python3
"""Minimal euc bot: joins a table and plays random legal moves.

Usage:
    pip install websockets requests
    python bot.py https://euc.example.ts.net --password sekrit --table MAIN --seat 2

The entire strategy surface is `view["legal"]`: when it's non-empty, send one
of its elements back wrapped in an `act` message. See ../PROTOCOL.md.
"""

import argparse
import asyncio
import json
import random

import requests
import websockets


async def run(base_url: str, password: str | None, table: str, seat: int, name: str) -> None:
    token = None
    if password is not None:
        resp = requests.post(f"{base_url}/api/login", json={"password": password})
        resp.raise_for_status()
        token = resp.json()["token"]

    ws_url = base_url.replace("http", "ws", 1) + "/ws"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with websockets.connect(ws_url, additional_headers=headers) as ws:
        async def send(msg: dict) -> None:
            await ws.send(json.dumps(msg))

        await send({"type": "hello", "name": name})
        await send({"type": "join_table", "table_id": table,
                    "role": {"type": "seated", "seat": seat}})

        async for frame in ws:
            msg = json.loads(frame)
            if msg["type"] == "error":
                print("server says:", msg["code"], "-", msg["message"])
            elif msg["type"] == "table_state":
                legal = msg["view"]["legal"]
                if legal:
                    action = random.choice(legal)
                    print("acting:", action)
                    await send({"type": "act", "action": action})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="e.g. https://euc.example.ts.net or http://localhost:8090")
    parser.add_argument("--password", default=None, help="site password (omit on a dev server)")
    parser.add_argument("--table", default="MAIN")
    parser.add_argument("--seat", type=int, default=1, choices=range(4))
    parser.add_argument("--name", default="RandomBot")
    args = parser.parse_args()
    asyncio.run(run(args.url.rstrip("/"), args.password, args.table, args.seat, args.name))
