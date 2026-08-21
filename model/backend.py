"""Model contract: video → scene.glb + flythrough.mp4."""

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


def flythrough_path(job_id: str) -> Path:
    return job_path(job_id) / "flythrough.mp4"


def attach_file(job_id: str, dest: Path, source: Path | bytes, empty_msg: str) -> Path:
    if isinstance(source, bytes):
        dest.write_bytes(source)
    else:
        shutil.copyfile(source, dest)
    if dest.stat().st_size == 0:
        dest.unlink(missing_ok=True)
        raise ValueError(empty_msg)
    return dest


def attach_glb(job_id: str, source: Path | bytes, filename: str = "scene.glb") -> Path:
    if not filename.lower().endswith(".glb"):
        raise ValueError("Expected a .glb file")
    return attach_file(job_id, glb_path(job_id), source, "GLB file is empty")


def attach_flythrough(job_id: str, source: Path | bytes, filename: str = "flythrough.mp4") -> Path:
    lower = filename.lower()
    if not (lower.endswith(".mp4") or lower.endswith(".webm") or lower.endswith(".mov")):
        raise ValueError("Expected a video file (.mp4 / .webm / .mov)")
    return attach_file(job_id, flythrough_path(job_id), source, "Flythrough file is empty")


def describe_backend() -> dict[str, Any]:
    return {
        "inference": "colab_vggt",
        "weights": "https://huggingface.co/facebook/VGGT-1B",
        "notebook": "notebooks/colab_vggt_video_to_glb.ipynb",
        "outputs": ["scene.glb", "flythrough.mp4"],
        "note": (
            "End user should only use Streamlit. Until a GPU worker is automated, "
            "run the Colab notebook and attach both outputs to the job."
        ),
    }
