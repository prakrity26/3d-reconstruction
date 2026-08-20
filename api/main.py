"""API — video upload → (Colab model) → GLB download.

Model inference runs on Google Colab + Hugging Face VGGT.
This API stores the video, accepts the GLB back, and serves it.
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
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import ALLOWED_VIDEO_SUFFIXES, API_URL, MAX_UPLOAD_MB, PROCESS_SECONDS
from model.backend import attach_glb, describe_backend, glb_path, video_path

app = FastAPI(
    title="3D Reconstruction API",
    description="Upload video, run VGGT on Colab, upload GLB, download 3D.",
    version="0.3.0-model",
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
    has_glb: bool = False


def _public(job: dict[str, Any]) -> dict[str, Any]:
    jid = job["job_id"]
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
        has_glb=glb_path(jid).is_file(),
    ).model_dump()


def _update(job_id: str, **fields: Any) -> None:
    with _lock:
        job = _JOBS[job_id]
        job.update(fields)
        job["updated_at"] = _now()


def _prepare_job(job_id: str) -> None:
    """Local prep only — real neural net runs on Colab."""
    steps = [
        (0.25, "Video saved"),
        (0.55, "Ready for model"),
        (0.85, "Waiting for GLB from Colab"),
    ]
    try:
        _update(
            job_id,
            status="running",
            progress=0.05,
            step="Starting",
            message="Preparing your video…",
        )
        pause = max(PROCESS_SECONDS, 0.4) / len(steps)
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
            status="awaiting_glb",
            progress=1.0,
            step="Awaiting 3D from Colab",
            message=(
                "Video is ready. Run the Colab notebook (VGGT / Hugging Face), "
                "then upload the downloaded scene.glb for this job."
            ),
            result={
                "backend": describe_backend(),
                "next": "Upload scene.glb for this job_id",
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
        "phase": "model_colab_vggt",
        "api_url": API_URL,
        "max_upload_mb": MAX_UPLOAD_MB,
        "model": describe_backend(),
        "modules": {
            "ui": "live",
            "api": "live",
            "database": "pending (filesystem jobs/)",
            "queueing": "pending (background thread)",
            "model": "live (Colab + Hugging Face VGGT)",
        },
    }


@app.post("/v1/jobs", response_model=JobRecord, status_code=202)
async def create_job(video: UploadFile = File(...)) -> dict[str, Any]:
    filename = video.filename or "upload.mp4"
    suffix = Path(filename).suffix.lower() or ".mp4"
    if suffix not in ALLOWED_VIDEO_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported type '{suffix}'. Allowed: {sorted(ALLOWED_VIDEO_SUFFIXES)}",
        )

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
                    raise HTTPException(
                        status_code=413,
                        detail=f"Video must be smaller than {MAX_UPLOAD_MB} MB.",
                    )
                out.write(chunk)
        if written == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise

    now = _now()
    record = {
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
    with _lock:
        _JOBS[job_id] = record

    threading.Thread(
        target=_prepare_job,
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
        raise HTTPException(status_code=404, detail="Video file missing.")
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=job.get("original_filename") or path.name,
    )


@app.post("/v1/jobs/{job_id}/glb", response_model=JobRecord)
async def upload_glb(job_id: str, glb: UploadFile = File(...)) -> dict[str, Any]:
    with _lock:
        job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job_id.")

    name = glb.filename or "scene.glb"
    if not name.lower().endswith(".glb"):
        raise HTTPException(status_code=400, detail="Upload a .glb file")

    data = await glb.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty GLB")

    try:
        attach_glb(job_id, data, filename=name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _update(
        job_id,
        status="succeeded",
        progress=1.0,
        step="Done",
        message="3D reconstruction attached",
        error=None,
        result={
            "format": "glb",
            "download": f"/v1/jobs/{job_id}/glb",
            "backend": describe_backend(),
        },
    )
    with _lock:
        return _public(_JOBS[job_id])


@app.get("/v1/jobs/{job_id}/glb")
def download_glb(job_id: str) -> FileResponse:
    with _lock:
        job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job_id.")
    path = glb_path(job_id)
    if not path.is_file():
        raise HTTPException(
            status_code=409,
            detail="GLB not ready. Run Colab and upload scene.glb first.",
        )
    return FileResponse(
        path,
        media_type="model/gltf-binary",
        filename=f"{job_id}.glb",
    )
