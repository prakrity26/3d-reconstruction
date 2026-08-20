"""UI module — upload a video, watch processing, see Hello World.

Run:
    streamlit run ui/app.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx
import streamlit as st

from config import API_URL, MAX_UPLOAD_MB

st.set_page_config(
    page_title="3D Reconstruction",
    page_icon="🧊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Source+Sans+3:wght@400;500;600;700&display=swap');

:root {{
  --ink: #0e1a22;
  --muted: #5a6d7a;
  --panel: rgba(248, 251, 253, 0.92);
  --line: rgba(14, 26, 34, 0.10);
  --accent: #0d6e6e;
}}

html, body, [data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(1100px 560px at 8% -15%, #cfe8ea 0%, transparent 55%),
    radial-gradient(900px 480px at 100% 5%, #d5e0f0 0%, transparent 48%),
    linear-gradient(165deg, #e7eef3 0%, #f5f8fb 42%, #e9f1f2 100%);
  color: var(--ink);
  font-family: "Source Sans 3", sans-serif;
}}

[data-testid="stHeader"] {{ background: transparent; }}

.block-container {{
  max-width: 760px;
  padding-top: 2.2rem;
  padding-bottom: 4rem;
}}

.hero-brand {{
  font-family: "Fraunces", serif;
  font-size: clamp(2.3rem, 5vw, 3.2rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
  margin: 0 0 0.5rem 0;
}}

.hero-line {{
  font-size: 1.08rem;
  color: var(--muted);
  max-width: 34rem;
  margin: 0 0 1.5rem 0;
}}

.steps {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.65rem;
  margin: 0 0 1.5rem 0;
}}

.step {{
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 14px;
  padding: 0.85rem 0.95rem;
}}

.step .n {{
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}}

.step .t {{
  font-family: "Fraunces", serif;
  font-size: 1.05rem;
  font-weight: 600;
}}

.step.active {{
  border-color: rgba(13, 110, 110, 0.45);
  box-shadow: 0 0 0 3px rgba(13, 110, 110, 0.12);
}}

.step.done {{ border-color: rgba(31, 122, 77, 0.35); }}

.panel {{
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 18px;
  padding: 1.25rem 1.35rem 1.35rem;
}}

.panel h3 {{
  font-family: "Fraunces", serif;
  font-size: 1.3rem;
  margin: 0 0 0.35rem 0;
}}

.panel p {{ color: var(--muted); margin: 0 0 0.75rem 0; }}

.result-card {{
  border: 1px solid rgba(13, 110, 110, 0.28);
  background: linear-gradient(180deg, #ffffff 0%, #eef7f7 100%);
  border-radius: 18px;
  padding: 1.45rem 1.35rem;
  text-align: center;
  margin-top: 0.5rem;
}}

.result-card .label {{
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
}}

.result-card .hello {{
  font-family: "Fraunces", serif;
  font-size: clamp(2rem, 5vw, 2.7rem);
  font-weight: 700;
  margin: 0.35rem 0 0.45rem 0;
}}

.status-pill {{
  display: inline-block;
  border-radius: 999px;
  padding: 0.28rem 0.75rem;
  font-size: 0.85rem;
  font-weight: 600;
  background: rgba(13, 110, 110, 0.12);
  color: var(--accent);
}}

.hint {{
  font-size: 0.9rem;
  color: var(--muted);
  margin-top: 1.75rem;
}}

div[data-testid="stFileUploader"] section {{
  border: 1.5px dashed rgba(14, 26, 34, 0.22) !important;
  background: rgba(255,255,255,0.55) !important;
  border-radius: 14px !important;
}}

.stButton > button {{
  border-radius: 12px !important;
  font-weight: 600 !important;
}}

footer {{ visibility: hidden; }}
</style>
""",
    unsafe_allow_html=True,
)


def api_get(path: str, timeout: float = 10.0) -> httpx.Response:
    return httpx.get(f"{API_URL}{path}", timeout=timeout)


def api_post(path: str, **kwargs) -> httpx.Response:
    return httpx.post(f"{API_URL}{path}", timeout=kwargs.pop("timeout", 120.0), **kwargs)


def stage() -> str:
    job = st.session_state.get("job")
    if job and job.get("status") == "succeeded":
        return "result"
    if st.session_state.get("job_id"):
        return "processing"
    return "upload"


def render_steps(current: str) -> None:
    order = ["upload", "processing", "result"]
    labels = {
        "upload": ("01", "Upload"),
        "processing": ("02", "Processing"),
        "result": ("03", "Result"),
    }
    idx = order.index(current)
    cells = []
    for i, key in enumerate(order):
        n, t = labels[key]
        cls = "step"
        if i == idx:
            cls += " active"
        elif i < idx:
            cls += " done"
        cells.append(
            f'<div class="{cls}"><div class="n">Step {n}</div><div class="t">{t}</div></div>'
        )
    st.markdown(f'<div class="steps">{"".join(cells)}</div>', unsafe_allow_html=True)


st.markdown('<p class="hero-brand">3D Reconstruction</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-line">'
    "Upload a video. We show processing so you never feel stuck. "
    "For now the API returns <strong>Hello World</strong> — real 3D comes later."
    "</p>",
    unsafe_allow_html=True,
)

current = stage()
render_steps(current)

try:
    api_ok = bool(api_get("/health").json().get("ok"))
except Exception:
    api_ok = False

if not api_ok:
    st.error(
        "API is not reachable. In another terminal run:\n\n"
        "`uvicorn api.main:app --host 127.0.0.1 --port 8000`"
    )
    st.stop()

if current == "upload":
    st.markdown(
        f"""
<div class="panel">
  <h3>Choose your video</h3>
  <p>MP4, MOV, WEBM, MKV, AVI, or M4V. Maximum size <strong>{MAX_UPLOAD_MB} MB</strong>.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    video = st.file_uploader(
        "Video",
        type=["mp4", "mov", "avi", "mkv", "webm", "m4v"],
        label_visibility="collapsed",
    )
    if video is not None:
        size_mb = len(video.getvalue()) / (1024 * 1024)
        st.caption(f"Selected: **{video.name}** · {size_mb:.1f} MB")
        if size_mb > MAX_UPLOAD_MB:
            st.error(
                f"This file is {size_mb:.1f} MB. Choose one under {MAX_UPLOAD_MB} MB."
            )
        elif st.button("Start processing", type="primary", use_container_width=True):
            with st.spinner("Uploading…"):
                try:
                    files = {
                        "video": (
                            video.name,
                            video.getvalue(),
                            video.type or "video/mp4",
                        )
                    }
                    resp = api_post("/v1/jobs", files=files)
                    if resp.status_code >= 400:
                        content_type = resp.headers.get("content-type", "")
                        if "application/json" in content_type:
                            detail = resp.json().get("detail")
                        else:
                            detail = resp.text
                        st.error(detail or resp.text)
                    else:
                        payload = resp.json()
                        st.session_state.job_id = payload["job_id"]
                        st.session_state.job = payload
                        st.rerun()
                except Exception as exc:
                    st.error(f"Upload failed: {exc}")
    else:
        st.caption(f"Tip: a short clip under {MAX_UPLOAD_MB} MB is enough for this step.")

elif current == "processing":
    job_id = st.session_state["job_id"]
    st.markdown(
        """
<div class="panel">
  <h3>Video is processing</h3>
  <p>Stay here — we will move you to the result when it is ready.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    try:
        job = api_get(f"/v1/jobs/{job_id}").json()
        st.session_state.job = job
    except Exception as exc:
        st.error(f"Could not read status: {exc}")
        if st.button("Start over"):
            st.session_state.clear()
            st.rerun()
        st.stop()

    st.progress(min(max(float(job.get("progress") or 0.0), 0.0), 1.0))
    st.markdown(
        f'<span class="status-pill">{(job.get("status") or "").upper()}</span>'
        f'&nbsp;&nbsp;**{job.get("step") or "Working…"}**',
        unsafe_allow_html=True,
    )
    st.write(job.get("message") or "Video is processing…")
    st.caption(f"Job `{job_id}` · `{job.get('original_filename') or '—'}`")

    if job.get("status") == "failed":
        st.error(job.get("error") or "Processing failed.")
        if st.button("Try another video", type="primary"):
            st.session_state.clear()
            st.rerun()
    elif job.get("status") == "succeeded":
        st.rerun()
    else:
        time.sleep(0.8)
        st.rerun()

else:
    job = st.session_state.get("job") or {}
    result = job.get("result") or {}
    hello = result.get("text") or "Hello World"
    st.markdown(
        f"""
<div class="result-card">
  <div class="label">API response</div>
  <p class="hello">{hello}</p>
  <p style="color:#5a6d7a;margin:0;">Video upload → process → response works. Next modules: database, queueing, model.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    with st.expander("Job details"):
        st.json(
            {
                "job_id": job.get("job_id"),
                "status": job.get("status"),
                "original_filename": job.get("original_filename"),
                "size_bytes": job.get("size_bytes"),
                "result": result,
            }
        )
    if st.button("Process another video", type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown(
    f'<p class="hint">UI + API · video · max {MAX_UPLOAD_MB} MB · {API_URL}</p>',
    unsafe_allow_html=True,
)
