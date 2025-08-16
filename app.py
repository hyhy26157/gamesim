
import asyncio
import json
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.sim.world import World

# Load config
with open("config.json","r") as f:
    CFG = json.load(f)

app = FastAPI()

THIS_FILE = Path(__file__).resolve()
THIS_DIR = THIS_FILE.parent
CLIENT_DIR = THIS_DIR / "src" / "client"

app.mount("/client", StaticFiles(directory=CLIENT_DIR), name="client")

clients = {}
world = World(CFG)

async def simulation_task():
    tick_ms = CFG["TICK_MS"]
    while True:
        t0 = time.perf_counter()
        world.step()
        payload = world.snapshot()

        # enqueue to each client's queue
        for ws, q in list(clients.items()):
            try:
                q.put_nowait(payload)
            except Exception:
                clients.pop(ws, None)

        elapsed = (time.perf_counter() - t0) * 1000
        await asyncio.sleep(max(0, (tick_ms - elapsed) / 1000.0))

@app.on_event("startup")
async def on_start():
    asyncio.create_task(simulation_task())

@app.get("/")
async def index():
    # Serve a tiny HTML that loads the canvas client
    with open( CLIENT_DIR /"index.html","r") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    q: asyncio.Queue = asyncio.Queue(maxsize=5)  # small buffer
    clients[ws] = q

    # Push initial snapshot immediately
    await q.put(world.snapshot())

    try:
        while True:
            data = await q.get()
            await ws.send_json(data)
    except WebSocketDisconnect:
        pass
    except Exception:
        # Any send failure -> drop client
        pass
    finally:
        clients.pop(ws, None)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
