"""Shared settings for every module."""

from __future__ import annotations

import os

API_URL = os.environ.get("RECON_API_URL", "http://127.0.0.1:8000").rstrip("/")

# Reject oversized videos early (UI + API both enforce this).
MAX_UPLOAD_MB = int(os.environ.get("RECON_MAX_UPLOAD_MB", "200"))

ALLOWED_VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

# Fake processing duration until Queuing + Model modules exist.
PROCESS_SECONDS = float(os.environ.get("RECON_PROCESS_SECONDS", "3"))
