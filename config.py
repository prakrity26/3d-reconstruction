"""Shared settings for every module."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

API_URL = os.environ.get("RECON_API_URL", "http://127.0.0.1:8000").rstrip("/")

MAX_UPLOAD_MB = int(os.environ.get("RECON_MAX_UPLOAD_MB", "200"))
ALLOWED_VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

# Where uploaded videos + GLB outputs are stored (lightweight stand-in for Database).
JOBS_DIR = Path(os.environ.get("RECON_JOBS_DIR", REPO_ROOT / "jobs")).resolve()

# How long the local "processing" animation takes before the job waits for a GLB.
PROCESS_SECONDS = float(os.environ.get("RECON_PROCESS_SECONDS", "2"))
