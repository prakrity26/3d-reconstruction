"""Model contract used by the API.

Real neural inference happens on Colab (see notebooks/).
This module owns paths and GLB attachment so Database/Queueing can swap later
without changing the UI.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from config import JOBS_DIR


def jobs_dir() -> Path:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    return JOBS_DIR


def job_path(job_id: str) -> Path:
    path = jobs_dir() / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def video_path(job_id: str, suffix: str = ".mp4") -> Path:
    return job_path(job_id) / f"input{suffix}"


def glb_path(job_id: str) -> Path:
    return job_path(job_id) / "scene.glb"


def attach_glb(job_id: str, source: Path | bytes, filename: str = "scene.glb") -> Path:
    """Save a reconstructed GLB for a job (typically produced on Colab)."""
    dest = glb_path(job_id)
    if isinstance(source, bytes):
        dest.write_bytes(source)
    else:
        shutil.copyfile(source, dest)
    if dest.stat().st_size == 0:
        dest.unlink(missing_ok=True)
        raise ValueError("GLB file is empty")
    if not filename.lower().endswith(".glb"):
        raise ValueError("Expected a .glb file")
    return dest


def describe_backend() -> dict[str, Any]:
    return {
        "inference": "colab_vggt",
        "weights": "https://huggingface.co/facebook/VGGT-1B",
        "notebook": "notebooks/colab_vggt_video_to_glb.ipynb",
        "local_gpu": False,
        "note": "Run the Colab notebook on a GPU runtime, then upload the GLB to the API.",
    }
