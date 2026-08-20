"""API module — video upload → processing status → Hello World.

Modules:
  UI + API   → live on this branch
  Database   → in-memory jobs for now
  Queuing    → background thread stub
  Model      → Hello World (real 3D later)

    GET  /health
    POST /v1/jobs            upload video (< 200 MB)
    GET  /v1/jobs/{job_id}   poll status / result
"""

from __future__ import annotations

import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (
    ALLOWED_VIDEO_SUFFIXES,
    API_URL,
    MAX_UPLOAD_MB,
    PROCESS_SECONDS,
)

app = FastAPI(
    title="3D Reconstruction API",
    description=(
        "Upload a video, poll the job, get Hello World for now. "
        "Real 3D output arrives when the Model module is wired."
    ),
    version="0.2.0-video",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_lock = threading.Lock()
_JOBS: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobRecord(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    step: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    original_filename: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at: str
    updated_at: str
    result: Optional[dict[str, Any]] = None


def _public(job: dict[str, Any]) -> dict[str, Any]:
    return JobRecord(**{k: job.get(k) for k in JobRecord.model_fields}).model_dump()


def _update(job_id: str, **fields: Any) -> None:
    with _lock:
        job = _JOBS[job_id]
        job.update(fields)
        job["updated_at"] = _now()


def _simulate_process(job_id: str) -> None:
    """Stand-in for Queuing + Model. Ends with Hello World."""
    steps = [
        (0.15, "Video received"),
        (0.40, "Validating upload"),
        (0.70, "Processing video"),
        (0.90, "Preparing response"),
    ]
    try:
        _update(
            job_id,
            status="running",
            progress=0.05,
            step="Starting",
            message="Video is processing…",
        )
        pause = max(PROCESS_SECONDS, 0.5) / len(steps)
        for progress, step in steps:
            time.sleep(pause)
            _update(
                job_id,
                status="running",
                progress=progress,
                step=step,
                message="Video is processing…",
            )
        _update(
            job_id,
            status="succeeded",
            progress=1.0,
            step="Done",
            message="Finished",
            result={
                "text": "Hello World",
                "note": "Video path works. Next: database, queueing, then the real model.",
            },
        )
    except Exception as exc:  # pragma: no cover
        _update(
            job_id,
            status="failed",
            step="Failed",
            message="Something went wrong",
            error=f"{type(exc).__name__}: {exc}",
        )


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "video_hello_world",
        "api_url": API_URL,
        "max_upload_mb": MAX_UPLOAD_MB,
        "modules": {
            "ui": "live",
            "api": "live",
            "database": "pending (in-memory jobs)",
            "queueing": "pending (background thread)",
            "model": "pending (Hello World stub)",
        },
    }


@app.post("/v1/jobs", response_model=JobRecord, status_code=202)
async def create_job(
    video: UploadFile = File(..., description="Video, max 200 MB"),
) -> dict[str, Any]:
    filename = video.filename or "upload.mp4"
    suffix = Path(filename).suffix.lower() or ".mp4"
    if suffix not in ALLOWED_VIDEO_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported type '{suffix}'. Allowed: {sorted(ALLOWED_VIDEO_SUFFIXES)}",
        )

    limit = MAX_UPLOAD_MB * 1024 * 1024
    written = 0
    chunks: list[bytes] = []
    while True:
        chunk = await video.read(1024 * 1024)
        if not chunk:
            break
        written += len(chunk)
        if written > limit:
            raise HTTPException(
                status_code=413,
                detail=f"Video must be smaller than {MAX_UPLOAD_MB} MB.",
            )
        chunks.append(chunk)

    if written == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Not persisted yet — Database module will own storage later.
    _ = b"".join(chunks)

    job_id = uuid.uuid4().hex[:12]
    now = _now()
    record = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "step": "Queued",
        "message": "Upload accepted — waiting to process",
        "error": None,
        "original_filename": filename,
        "size_bytes": written,
        "created_at": now,
        "updated_at": now,
        "result": None,
    }
    with _lock:
        _JOBS[job_id] = record

    threading.Thread(
        target=_simulate_process,
        args=(job_id,),
        name=f"job-{job_id}",
        daemon=True,
    ).start()

    return _public(record)


@app.get("/v1/jobs/{job_id}", response_model=JobRecord)
def get_job(job_id: str) -> dict[str, Any]:
    with _lock:
        job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown job_id. Upload a video again.",
        )
    return _public(job)
