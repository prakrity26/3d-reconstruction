"""Shared settings for every module."""

from __future__ import annotations

import os

API_URL = os.environ.get("RECON_API_URL", "http://127.0.0.1:8000").rstrip("/")
