"""UI — upload video, guide Colab reconstruction, attach/download GLB."""

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
:root {{ --ink:#0e1a22; --muted:#5a6d7a; --panel:rgba(248,251,253,.92); --line:rgba(14,26,34,.10); --accent:#0d6e6e; }}
html, body, [data-testid="stAppViewContainer"] {{
  background: radial-gradient(1100px 560px at 8% -15%, #cfe8ea 0%, transparent 55%),
              radial-gradient(900px 480px at 100% 5%, #d5e0f0 0%, transparent 48%),
              linear-gradient(165deg, #e7eef3 0%, #f5f8fb 42%, #e9f1f2 100%);
  color: var(--ink); font-family: "Source Sans 3", sans-serif;
}}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ max-width: 760px; padding-top: 2.2rem; padding-bottom: 4rem; }}
.hero-brand {{ font-family: Fraunces, serif; font-size: clamp(2.3rem,5vw,3.2rem); font-weight:700; letter-spacing:-0.03em; margin:0 0 .5rem; }}
.hero-line {{ font-size:1.08rem; color:var(--muted); max-width:36rem; margin:0 0 1.4rem; }}
.steps {{ display:grid; grid-template-columns:repeat(4,1fr); gap:.55rem; margin:0 0 1.4rem; }}
.step {{ border:1px solid var(--line); background:var(--panel); border-radius:14px; padding:.75rem .85rem; }}
.step .n {{ font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); }}
.step .t {{ font-family:Fraunces,serif; font-size:.98rem; font-weight:600; }}
.step.active {{ border-color:rgba(13,110,110,.45); box-shadow:0 0 0 3px rgba(13,110,110,.12); }}
.step.done {{ border-color:rgba(31,122,77,.35); }}
.panel {{ border:1px solid var(--line); background:var(--panel); border-radius:18px; padding:1.2rem 1.3rem; }}
.panel h3 {{ font-family:Fraunces,serif; font-size:1.25rem; margin:0 0 .35rem; }}
.panel p {{ color:var(--muted); margin:0 0 .7rem; }}
.result-card {{ border:1px solid rgba(13,110,110,.28); background:linear-gradient(180deg,#fff,#eef7f7); border-radius:18px; padding:1.4rem; text-align:center; }}
.result-card .hello {{ font-family:Fraunces,serif; font-size:clamp(1.6rem,4vw,2.2rem); font-weight:700; margin:.35rem 0; }}
.status-pill {{ display:inline-block; border-radius:999px; padding:.28rem .75rem; font-size:.85rem; font-weight:600; background:rgba(13,110,110,.12); color:var(--accent); }}
.hint {{ font-size:.9rem; color:var(--muted); margin-top:1.6rem; }}
footer {{ visibility:hidden; }}
</style>
""",
    unsafe_allow_html=True,
)


def api_get(path: str, timeout: float = 30.0) -> httpx.Response:
    return httpx.get(f"{API_URL}{path}", timeout=timeout)


def api_post(path: str, **kwargs) -> httpx.Response:
    return httpx.post(f"{API_URL}{path}", timeout=kwargs.pop("timeout", 180.0), **kwargs)


def stage() -> str:
    job = st.session_state.get("job") or {}
    status = job.get("status")
    if status == "succeeded" or job.get("has_glb"):
        return "result"
    if status == "awaiting_glb":
        return "model"
    if st.session_state.get("job_id"):
        return "processing"
    return "upload"


def render_steps(current: str) -> None:
    order = ["upload", "processing", "model", "result"]
    labels = {
        "upload": ("01", "Upload"),
        "processing": ("02", "Prepare"),
        "model": ("03", "Colab 3D"),
        "result": ("04", "GLB"),
    }
    idx = order.index(current)
    cells = []
    for i, key in enumerate(order):
        n, t = labels[key]
        cls = "step" + (" active" if i == idx else " done" if i < idx else "")
        cells.append(f'<div class="{cls}"><div class="n">Step {n}</div><div class="t">{t}</div></div>')
    st.markdown(f'<div class="steps">{"".join(cells)}</div>', unsafe_allow_html=True)


st.markdown('<p class="hero-brand">3D Reconstruction</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-line">'
    "Upload a video. We prepare the job locally, then you run "
    "<strong>VGGT on Google Colab</strong> (weights from Hugging Face) and bring the GLB back."
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
    st.error("API is not reachable. Run: `uvicorn api.main:app --host 127.0.0.1 --port 8000`")
    st.stop()

if current == "upload":
    st.markdown(
        f'<div class="panel"><h3>Choose your video</h3>'
        f"<p>Max <strong>{MAX_UPLOAD_MB} MB</strong>. Short indoor clips work best on free Colab.</p></div>",
        unsafe_allow_html=True,
    )
    video = st.file_uploader("Video", type=["mp4", "mov", "avi", "mkv", "webm", "m4v"], label_visibility="collapsed")
    if video is not None:
        size_mb = len(video.getvalue()) / (1024 * 1024)
        st.caption(f"**{video.name}** · {size_mb:.1f} MB")
        if size_mb > MAX_UPLOAD_MB:
            st.error(f"File is {size_mb:.1f} MB. Keep it under {MAX_UPLOAD_MB} MB.")
        elif st.button("Start", type="primary", use_container_width=True):
            with st.spinner("Uploading…"):
                try:
                    files = {"video": (video.name, video.getvalue(), video.type or "video/mp4")}
                    resp = api_post("/v1/jobs", files=files)
                    if resp.status_code >= 400:
                        st.error(resp.text)
                    else:
                        payload = resp.json()
                        st.session_state.job_id = payload["job_id"]
                        st.session_state.job = payload
                        st.rerun()
                except Exception as exc:
                    st.error(f"Upload failed: {exc}")

elif current == "processing":
    job_id = st.session_state["job_id"]
    st.markdown(
        '<div class="panel"><h3>Preparing video</h3><p>Saving your upload and getting the job ready for Colab.</p></div>',
        unsafe_allow_html=True,
    )
    try:
        job = api_get(f"/v1/jobs/{job_id}").json()
        st.session_state.job = job
    except Exception as exc:
        st.error(f"Status error: {exc}")
        st.stop()
    st.progress(min(max(float(job.get("progress") or 0), 0), 1))
    st.markdown(
        f'<span class="status-pill">{(job.get("status") or "").upper()}</span> **{job.get("step") or "…"}**',
        unsafe_allow_html=True,
    )
    st.write(job.get("message") or "")
    if job.get("status") == "failed":
        st.error(job.get("error") or "Failed")
    elif job.get("status") in {"awaiting_glb", "succeeded"}:
        st.rerun()
    else:
        time.sleep(0.8)
        st.rerun()

elif current == "model":
    job = st.session_state.get("job") or {}
    job_id = job.get("job_id") or st.session_state.get("job_id")
    st.markdown(
        """
<div class="panel">
  <h3>Run the model on Google Colab</h3>
  <p>Your Mac has no CUDA GPU, so reconstruction uses <strong>VGGT</strong> on Colab with weights from Hugging Face.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
1. Download your video from the API: [{API_URL}/v1/jobs/{job_id}/video]({API_URL}/v1/jobs/{job_id}/video)
2. Open `notebooks/colab_vggt_video_to_glb.ipynb` in [Google Colab](https://colab.research.google.com/)
3. Runtime → **GPU**
4. Run all cells → download `scene.glb`
5. Upload that GLB below
"""
    )
    glb = st.file_uploader("Upload scene.glb from Colab", type=["glb"])
    if glb is not None and st.button("Attach 3D result", type="primary", use_container_width=True):
        with st.spinner("Uploading GLB…"):
            try:
                files = {"glb": (glb.name, glb.getvalue(), "model/gltf-binary")}
                resp = api_post(f"/v1/jobs/{job_id}/glb", files=files)
                if resp.status_code >= 400:
                    st.error(resp.text)
                else:
                    st.session_state.job = resp.json()
                    st.rerun()
            except Exception as exc:
                st.error(f"GLB upload failed: {exc}")
    if st.button("Refresh status"):
        st.session_state.job = api_get(f"/v1/jobs/{job_id}").json()
        st.rerun()

else:
    job = st.session_state.get("job") or {}
    job_id = job.get("job_id")
    st.markdown(
        """
<div class="result-card">
  <p class="hello">3D ready</p>
  <p style="color:#5a6d7a;margin:0;">Your GLB is attached. Download it and open in Blender, a web viewer, or any glTF tool.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    try:
        glb_resp = api_get(f"/v1/jobs/{job_id}/glb", timeout=60.0)
        if glb_resp.status_code == 200:
            st.download_button(
                "Download scene.glb",
                data=glb_resp.content,
                file_name=f"{job_id}.glb",
                mime="model/gltf-binary",
                type="primary",
                use_container_width=True,
            )
        else:
            st.warning(glb_resp.text)
    except Exception as exc:
        st.error(f"Could not fetch GLB: {exc}")
    if st.button("New video", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown(
    f'<p class="hint">Model module · Colab + Hugging Face VGGT · {API_URL}</p>',
    unsafe_allow_html=True,
)
