"""FastAPI backend — REST compute + WebSocket sync, and it serves the client.

Every successful /api/compute is broadcast to all connected WebSocket clients,
so the React client (and any number of browser tabs) stay in sync with the
latest computation in real time.

The React page in ``web/`` is mounted at ``/app``, so a single process serves
both the API and the UI:

    uvicorn server.app:app --reload --port 8000
    open http://localhost:8000/app
"""

import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from omnidimensional import (  # noqa: E402
    Arithmetic, Geometric, Harmonic, FAMILY_NAMES, MAX_N, MAX_POWER,
    power_mean_spectrum, omnidimensional_midpoint, verify, __version__,
)
from omnidimensional.engine import POWER_FORM, ComputeError, compute  # noqa: E402

app = FastAPI(title="omnidimensional", version=__version__)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


class ComputeRequest(BaseModel):
    family: str = "geometric"          # arithmetic | geometric | harmonic | power
    n: int = Field(default=100, ge=0, le=MAX_N)
    a: float = 1.0
    d: float = 1.0
    r: float = 2.0
    p: int = Field(default=2, ge=0, le=MAX_POWER)
    client: str = "anon"


class Hub:
    """Fan-out of the latest computation to every connected browser tab."""

    def __init__(self):
        self.clients: List[WebSocket] = []
        self.last: Optional[dict] = None

    async def join(self, ws: WebSocket):
        await ws.accept()
        self.clients.append(ws)
        await ws.send_json({"type": "state",
                            "payload": self.last or {"note": "no computation yet"}})

    def leave(self, ws: WebSocket):
        if ws in self.clients:
            self.clients.remove(ws)

    async def broadcast(self, payload):
        self.last = payload
        dead = []
        for ws in self.clients:
            try:
                await ws.send_json({"type": "update", "payload": payload})
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.leave(ws)


hub = Hub()


@app.get("/api/health")
def health():
    return {"ok": True, "version": __version__, "clients": len(hub.clients)}


@app.get("/api/families")
def families():
    return {
        "arithmetic": Arithmetic.closed_form,
        "geometric": Geometric.closed_form,
        "harmonic": Harmonic.closed_form,
        "power": POWER_FORM,
    }


@app.get("/api/spectrum")
def spectrum(values: str = "3,5,11,2"):
    try:
        vals = [float(x) for x in values.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(422, "values must be a comma-separated list of numbers")
    if not vals:
        raise HTTPException(422, "values must contain at least one number")
    return {str(int(p)): v for p, v in power_mean_spectrum(vals).items()}


@app.get("/api/midpoint")
def midpoint(a: float, b: float, family: str = "harmonic"):
    try:
        value = omnidimensional_midpoint(a, b, family)
    except (ValueError, ZeroDivisionError) as exc:
        raise HTTPException(422, str(exc))
    return {"midpoint": float(value), "family": family}


@app.get("/api/verify")
def verify_endpoint(family: str, n: int = 100, a: float = 1.0, d: float = 1.0,
                    r: float = 2.0, p: int = 2):
    if family not in FAMILY_NAMES:
        raise HTTPException(422, "unknown family: %r" % family)
    try:
        return verify(family, n, a=a, d=d, r=r, p=p)
    except (ValueError, ZeroDivisionError) as exc:
        raise HTTPException(422, str(exc))


@app.post("/api/compute")
async def compute_endpoint(req: ComputeRequest):
    try:
        out = compute(req.family, req.n, a=req.a, d=req.d, r=req.r, p=req.p)
    except ComputeError as exc:
        raise HTTPException(422, str(exc))
    except (ZeroDivisionError, OverflowError) as exc:
        raise HTTPException(422, "%s: %s" % (type(exc).__name__, exc))
    out["client"] = req.client
    await hub.broadcast(out)     # push to every synced client
    return out


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await hub.join(ws)
    try:
        while True:
            await ws.receive_text()   # keepalive; clients may ping
    except WebSocketDisconnect:
        hub.leave(ws)
    except Exception:
        hub.leave(ws)


WEB_DIR = ROOT / "web"
if WEB_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


@app.get("/")
def root():
    if WEB_DIR.is_dir():
        return RedirectResponse("/app/")
    return HTMLResponse("<h3>omnidimensional API</h3>"
                        "<p>POST /api/compute · GET /api/families · WS /ws</p>")
