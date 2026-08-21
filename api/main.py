"""API — upload video → (GPU model) → scene.glb + flythrough.mp4."""

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
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import ALLOWED_VIDEO_SUFFIXES, API_URL, MAX_UPLOAD_MB, PROCESS_SECONDS
from model.backend import (
    attach_flythrough,
    attach_glb,
    describe_backend,
    flythrough_path,
    glb_path,
    video_path,
)

app = FastAPI(
    title="3D Reconstruction API",
    description="Upload a video; get interactive GLB + flythrough MP4 for that video.",
    version="0.4.0-dual-outputs",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
    has_glb: bool = False
    has_flythrough: bool = False


def _public(job: dict[str, Any]) -> dict[str, Any]:
    jid = job["job_id"]
    has_glb = glb_path(jid).is_file()
    has_ft = flythrough_path(jid).is_file()
    return JobRecord(
        job_id=jid,
        status=job["status"],
        progress=job.get("progress", 0.0),
        step=job.get("step"),
        message=job.get("message"),
        error=job.get("error"),
        original_filename=job.get("original_filename"),
        size_bytes=job.get("size_bytes"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        result=job.get("result"),
        has_glb=has_glb,
        has_flythrough=has_ft,
    ).model_dump()


def _update(job_id: str, **fields: Any) -> None:
    with _lock:
        _JOBS[job_id].update(fields)
        _JOBS[job_id]["updated_at"] = _now()


def _refresh_status(job_id: str) -> None:
    """Mark succeeded only when BOTH outputs exist."""
    has_glb = glb_path(job_id).is_file()
    has_ft = flythrough_path(job_id).is_file()
    if has_glb and has_ft:
        _update(
            job_id,
            status="succeeded",
            progress=1.0,
            step="Done",
            message="3D ready: interactive GLB + flythrough video",
            error=None,
            result={
                "glb": f"/v1/jobs/{job_id}/glb",
                "flythrough": f"/v1/jobs/{job_id}/flythrough",
                "backend": describe_backend(),
            },
        )
    elif has_glb or has_ft:
        missing = "flythrough.mp4" if has_glb else "scene.glb"
        _update(
            job_id,
            status="awaiting_artifacts",
            step="Waiting for both outputs",
            message=f"Received one file. Still need {missing}.",
        )


def _prepare_job(job_id: str) -> None:
    steps = [(0.3, "Video saved"), (0.6, "Queued for 3D reconstruction"), (0.9, "Waiting for model outputs")]
    try:
        _update(job_id, status="running", progress=0.05, step="Starting", message="Preparing your video…")
        pause = max(PROCESS_SECONDS, 0.4) / len(steps)
        for progress, step in steps:
            time.sleep(pause)
            _update(job_id, status="running", progress=progress, step=step, message="Video is processing…")
        _update(
            job_id,
            status="awaiting_artifacts",
            progress=1.0,
            step="Awaiting GLB + flythrough",
            message=(
                "Video is ready for reconstruction. Until the GPU worker is automatic, "
                "run the Colab notebook on this video and upload scene.glb + flythrough.mp4 here."
            ),
            result={"backend": describe_backend()},
        )
    except Exception as exc:  # pragma: no cover
        _update(job_id, status="failed", step="Failed", message="Something went wrong", error=f"{type(exc).__name__}: {exc}")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "dual_outputs",
        "api_url": API_URL,
        "max_upload_mb": MAX_UPLOAD_MB,
        "outputs": ["scene.glb", "flythrough.mp4"],
        "model": describe_backend(),
    }


@app.post("/v1/jobs", response_model=JobRecord, status_code=202)
async def create_job(video: UploadFile = File(...)) -> dict[str, Any]:
    filename = video.filename or "upload.mp4"
    suffix = Path(filename).suffix.lower() or ".mp4"
    if suffix not in ALLOWED_VIDEO_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"Unsupported type '{suffix}'")

    limit = MAX_UPLOAD_MB * 1024 * 1024
    job_id = uuid.uuid4().hex[:12]
    dest = video_path(job_id, suffix)
    written = 0
    try:
        with dest.open("wb") as out:
            while True:
                chunk = await video.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > limit:
                    raise HTTPException(status_code=413, detail=f"Video must be smaller than {MAX_UPLOAD_MB} MB.")
                out.write(chunk)
        if written == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise

    now = _now()
    with _lock:
        _JOBS[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0.0,
            "step": "Queued",
            "message": "Upload accepted",
            "error": None,
            "original_filename": filename,
            "size_bytes": written,
            "created_at": now,
            "updated_at": now,
            "result": None,
            "video_suffix": suffix,
        }
    threading.Thread(target=_prepare_job, args=(job_id,), daemon=True).start()
    return _public(_JOBS[job_id])


@app.get("/v1/jobs/{job_id}", response_model=JobRecord)
def get_job(job_id: str) -> dict[str, Any]:
    with _lock:
        job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job_id.")
    return _public(job)


@app.get("/v1/jobs/{job_id}/video")
def download_video(job_id: str) -> FileResponse:
    with _lock:
        job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job_id.")
    path = video_path(job_id, job.get("video_suffix", ".mp4"))
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Video missing")
    return FileResponse(path, media_type="application/octet-stream", filename=job.get("original_filename") or path.name)


@app.post("/v1/jobs/{job_id}/glb", response_model=JobRecord)
async def upload_glb(job_id: str, glb: UploadFile = File(...)) -> dict[str, Any]:
    with _lock:
        if job_id not in _JOBS:
            raise HTTPException(status_code=404, detail="Unknown job_id.")
    name = glb.filename or "scene.glb"
    data = await glb.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty GLB")
    try:
        attach_glb(job_id, data, filename=name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _refresh_status(job_id)
    with _lock:
        return _public(_JOBS[job_id])


@app.post("/v1/jobs/{job_id}/flythrough", response_model=JobRecord)
async def upload_flythrough(job_id: str, video: UploadFile = File(...)) -> dict[str, Any]:
    with _lock:
        if job_id not in _JOBS:
            raise HTTPException(status_code=404, detail="Unknown job_id.")
    name = video.filename or "flythrough.mp4"
    data = await video.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty flythrough")
    try:
        attach_flythrough(job_id, data, filename=name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _refresh_status(job_id)
    with _lock:
        return _public(_JOBS[job_id])


@app.get("/v1/jobs/{job_id}/glb")
def download_glb(job_id: str) -> FileResponse:
    path = glb_path(job_id)
    if not path.is_file():
        raise HTTPException(status_code=409, detail="GLB not ready yet")
    return FileResponse(path, media_type="model/gltf-binary", filename=f"{job_id}.glb")


@app.get("/v1/jobs/{job_id}/flythrough")
def download_flythrough(job_id: str) -> FileResponse:
    path = flythrough_path(job_id)
    if not path.is_file():
        raise HTTPException(status_code=409, detail="Flythrough not ready yet")
    return FileResponse(path, media_type="video/mp4", filename=f"{job_id}_flythrough.mp4")
