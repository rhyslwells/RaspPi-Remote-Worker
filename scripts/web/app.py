#!/usr/bin/env python3
"""
Pi Control: a small web UI for running and watching the task scripts.

    python scripts/web/app.py          # binds 127.0.0.1:8051 unless PI_CONTROL_HOST is set

Reach it only over Tailscale (set PI_CONTROL_HOST to the Pi's Tailscale address) or on
localhost. It must never be exposed to the internet. For local trying-out with demo
scripts use debug_control.py at the repo root. Design: docs/pi-control.md.
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from web import engine  # noqa: E402

PAGE = Path(__file__).resolve().parent / "static" / "index.html"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    engine.reconcile()
    yield


app = FastAPI(title="Pi Control", lifespan=lifespan)


@app.middleware("http")
async def require_header(request: Request, call_next):
    """
    Refuse any change request without our own header. A page on another site cannot
    add a custom header without a CORS preflight, which this app never allows, so this
    stops a web page you happen to have open from firing runs at the Pi.
    """
    if request.method not in ("GET", "HEAD") and request.headers.get("x-pi-control") != "1":
        return JSONResponse({"message": "Missing X-Pi-Control header"}, status_code=403)
    return await call_next(request)


@app.exception_handler(engine.EngineError)
async def engine_error(_request: Request, exc: engine.EngineError):
    return JSONResponse({"message": exc.message, "errors": exc.errors}, status_code=exc.status)


class RunRequest(BaseModel):
    params: Dict[str, Any] = Field(default_factory=dict)
    confirm: bool = False


@app.get("/")
def index():
    return FileResponse(PAGE, headers={"Cache-Control": "no-store"})


@app.get("/api/scripts")
def scripts():
    return engine.list_scripts()


@app.get("/api/runs")
def runs(limit: int = 20, script: str = ""):
    return engine.list_runs(limit, script or None)


@app.get("/api/runs/{run_id}")
def run_detail(run_id: int):
    return engine.get_run(run_id)


@app.get("/api/log/{run_id}")
def log(run_id: int):
    return engine.read_log(run_id)


@app.post("/api/run/{name}")
def run(name: str, req: RunRequest):
    return engine.start_run(name, req.params, req.confirm)


@app.post("/api/stop/{name}")
def stop(name: str):
    return engine.stop_run(name)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.environ.get("PI_CONTROL_HOST", "127.0.0.1"),
        port=int(os.environ.get("PI_CONTROL_PORT", "8051")),
    )
