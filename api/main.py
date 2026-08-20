"""API module (Phase 1) — text in, Hello World out.

Later modules (database, queueing, model) plug in behind this contract.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import API_URL

app = FastAPI(
    title="3D Reconstruction API",
    description="Phase 1: text Hello World. Video and 3D come in later modules.",
    version="0.1.0-phase1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class HelloRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


class HelloResponse(BaseModel):
    input: str
    message: str
    note: str


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": 1,
        "mode": "hello_world_text",
        "api_url": API_URL,
        "modules": {
            "ui": "live",
            "api": "live",
            "database": "pending",
            "queueing": "pending",
            "model": "pending",
        },
    }


@app.post("/v1/hello", response_model=HelloResponse)
def hello(body: HelloRequest) -> HelloResponse:
    return HelloResponse(
        input=body.text.strip(),
        message="Hello World",
        note="Phase 1 — UI + API only. More modules come next.",
    )
