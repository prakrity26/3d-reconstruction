"""UI — upload video → processing → download GLB + flythrough MP4."""

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

st.set_page_config(page_title="3D Reconstruction", page_icon="🧊", layout="centered", initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Source+Sans+3:wght@400;500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1100px 560px at 8% -15%, #cfe8ea 0%, transparent 55%),
              linear-gradient(165deg, #e7eef3 0%, #f5f8fb 45%, #e9f1f2 100%);
  font-family: "Source Sans 3", sans-serif; color: #0e1a22;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 760px; padding-top: 2rem; }
.hero { font-family: Fraunces, serif; font-size: clamp(2.2rem,5vw,3.1rem); font-weight: 700; margin: 0 0 .4rem; }
.sub { color: #5a6d7a; font-size: 1.05rem; margin: 0 0 1.2rem; max-width: 38rem; }
.panel { background: rgba(248,251,253,.92); border: 1px solid rgba(14,26,34,.1); border-radius: 16px; padding: 1.1rem 1.2rem; margin-bottom: 1rem; }
.panel h3 { font-family: Fraunces, serif; margin: 0 0 .35rem; }
.panel p { color: #5a6d7a; margin: 0; }
.pill { display:inline-block; background:rgba(13,110,110,.12); color:#0d6e6e; border-radius:999px; padding:.25rem .7rem; font-weight:600; font-size:.85rem; }
footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


def api_get(path: str, timeout: float = 60.0) -> httpx.Response:
    return httpx.get(f"{API_URL}{path}", timeout=timeout)


def api_post(path: str, **kwargs) -> httpx.Response:
    return httpx.post(f"{API_URL}{path}", timeout=kwargs.pop("timeout", 180.0), **kwargs)


def stage() -> str:
    job = st.session_state.get("job") or {}
    if job.get("status") == "succeeded" and job.get("has_glb") and job.get("has_flythrough"):
        return "result"
    if job.get("status") in {"awaiting_artifacts", "awaiting_glb"} or job.get("has_glb") or job.get("has_flythrough"):
        return "artifacts"
    if st.session_state.get("job_id"):
        return "processing"
    return "upload"


st.markdown('<p class="hero">3D Reconstruction</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub">Upload one video. When processing finishes you get <strong>two</strong> outputs of that same video: '
    "an interactive 3D file (<code>scene.glb</code>) and a moving flythrough (<code>flythrough.mp4</code>).</p>",
    unsafe_allow_html=True,
)

current = stage()

try:
    if not api_get("/health").json().get("ok"):
        raise RuntimeError("unhealthy")
except Exception:
    st.error("Start the API first: `uvicorn api.main:app --host 127.0.0.1 --port 8000`")
    st.stop()

if current == "upload":
    st.markdown(
        f'<div class="panel"><h3>1. Upload your video</h3>'
        f"<p>Max {MAX_UPLOAD_MB} MB. Short indoor clips work best.</p></div>",
        unsafe_allow_html=True,
    )
    video = st.file_uploader("Video", type=["mp4", "mov", "avi", "mkv", "webm", "m4v"], label_visibility="collapsed")
    if video is not None:
        mb = len(video.getvalue()) / (1024 * 1024)
        st.caption(f"{video.name} · {mb:.1f} MB")
        if mb > MAX_UPLOAD_MB:
            st.error(f"Keep under {MAX_UPLOAD_MB} MB")
        elif st.button("Start processing", type="primary", use_container_width=True):
            with st.spinner("Uploading…"):
                resp = api_post("/v1/jobs", files={"video": (video.name, video.getvalue(), video.type or "video/mp4")})
                if resp.status_code >= 400:
                    st.error(resp.text)
                else:
                    st.session_state.job = resp.json()
                    st.session_state.job_id = st.session_state.job["job_id"]
                    st.rerun()

elif current == "processing":
    job_id = st.session_state["job_id"]
    st.markdown('<div class="panel"><h3>2. Video is processing</h3><p>Stay here — preparing your job.</p></div>', unsafe_allow_html=True)
    job = api_get(f"/v1/jobs/{job_id}").json()
    st.session_state.job = job
    st.progress(min(max(float(job.get("progress") or 0), 0), 1))
    st.markdown(f'<span class="pill">{job.get("status","").upper()}</span>  **{job.get("step") or ""}**', unsafe_allow_html=True)
    st.write(job.get("message") or "")
    if job.get("status") in {"awaiting_artifacts", "awaiting_glb", "succeeded"}:
        st.rerun()
    elif job.get("status") == "failed":
        st.error(job.get("error") or "Failed")
    else:
        time.sleep(0.8)
        st.rerun()

elif current == "artifacts":
    job = st.session_state.get("job") or {}
    job_id = job.get("job_id") or st.session_state.get("job_id")
    st.markdown(
        """
<div class="panel">
  <h3>3. Attach reconstruction outputs</h3>
  <p>Final product hides this step. For now (no automatic GPU on Mac), run <code>notebooks/colab_lingbot_video_to_glb.ipynb</code> on your uploaded video, then attach the LingBot <code>scene.glb</code> (and flythrough later).</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
1. Download the uploaded video: [{API_URL}/v1/jobs/{job_id}/video]({API_URL}/v1/jobs/{job_id}/video)
2. Open `notebooks/colab_lingbot_video_to_glb.ipynb` in Colab (**GPU**)
3. Run it → download **`scene.glb`** and **`flythrough.mp4`**
4. Upload both here
"""
    )
    c1, c2 = st.columns(2)
    with c1:
        st.write("Interactive 3D")
        st.caption("scene.glb ✓" if job.get("has_glb") else "scene.glb missing")
        glb = st.file_uploader("GLB", type=["glb"], key="glb")
        if glb and st.button("Upload GLB", use_container_width=True):
            resp = api_post(f"/v1/jobs/{job_id}/glb", files={"glb": (glb.name, glb.getvalue(), "model/gltf-binary")})
            st.session_state.job = resp.json() if resp.status_code < 400 else job
            if resp.status_code >= 400:
                st.error(resp.text)
            else:
                st.rerun()
    with c2:
        st.write("Flythrough video")
        st.caption("flythrough.mp4 ✓" if job.get("has_flythrough") else "flythrough.mp4 missing")
        ft = st.file_uploader("Flythrough", type=["mp4", "webm", "mov"], key="ft")
        if ft and st.button("Upload flythrough", use_container_width=True):
            resp = api_post(
                f"/v1/jobs/{job_id}/flythrough",
                files={"video": (ft.name, ft.getvalue(), ft.type or "video/mp4")},
            )
            st.session_state.job = resp.json() if resp.status_code < 400 else job
            if resp.status_code >= 400:
                st.error(resp.text)
            else:
                st.rerun()

    if st.button("Refresh status"):
        st.session_state.job = api_get(f"/v1/jobs/{job_id}").json()
        st.rerun()

else:
    job = st.session_state.get("job") or {}
    job_id = job.get("job_id")
    st.markdown(
        '<div class="panel"><h3>4. Your 3D outputs</h3>'
        "<p>Both files come from the video you uploaded.</p></div>",
        unsafe_allow_html=True,
    )
    glb = api_get(f"/v1/jobs/{job_id}/glb")
    ft = api_get(f"/v1/jobs/{job_id}/flythrough")
    if glb.status_code == 200:
        st.download_button("Download scene.glb (interactive 3D)", data=glb.content, file_name=f"{job_id}.glb", mime="model/gltf-binary", use_container_width=True)
    if ft.status_code == 200:
        st.video(ft.content)
        st.download_button("Download flythrough.mp4", data=ft.content, file_name=f"{job_id}_flythrough.mp4", mime="video/mp4", use_container_width=True)
    if st.button("New video", use_container_width=True):
        st.session_state.clear()
        st.rerun()
