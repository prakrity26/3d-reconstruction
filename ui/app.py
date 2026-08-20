"""UI module (Phase 1) — text form talking to the API.

Run:
    streamlit run ui/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx
import streamlit as st

from config import API_URL

st.set_page_config(
    page_title="3D Reconstruction",
    page_icon="🧊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Source+Sans+3:wght@400;500;600;700&display=swap');

:root {
  --ink: #0e1a22;
  --muted: #5a6d7a;
  --panel: rgba(248, 251, 253, 0.92);
  --line: rgba(14, 26, 34, 0.10);
  --accent: #0d6e6e;
}

html, body, [data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1100px 560px at 8% -15%, #cfe8ea 0%, transparent 55%),
    radial-gradient(900px 480px at 100% 5%, #d5e0f0 0%, transparent 48%),
    linear-gradient(165deg, #e7eef3 0%, #f5f8fb 42%, #e9f1f2 100%);
  color: var(--ink);
  font-family: "Source Sans 3", sans-serif;
}

[data-testid="stHeader"] { background: transparent; }

.block-container {
  max-width: 680px;
  padding-top: 2.4rem;
  padding-bottom: 4rem;
}

.hero-brand {
  font-family: "Fraunces", serif;
  font-size: clamp(2.3rem, 5vw, 3.2rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
  margin: 0 0 0.5rem 0;
}

.hero-line {
  font-size: 1.08rem;
  color: var(--muted);
  max-width: 32rem;
  margin: 0 0 1.75rem 0;
}

.panel {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 18px;
  padding: 1.25rem 1.35rem 1.4rem;
  margin-bottom: 1rem;
}

.panel h3 {
  font-family: "Fraunces", serif;
  font-size: 1.3rem;
  margin: 0 0 0.35rem 0;
}

.panel p { color: var(--muted); margin: 0; }

.result-card {
  border: 1px solid rgba(13, 110, 110, 0.28);
  background: linear-gradient(180deg, #ffffff 0%, #eef7f7 100%);
  border-radius: 18px;
  padding: 1.45rem 1.35rem;
  text-align: center;
  margin-top: 0.75rem;
}

.result-card .label {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
}

.result-card .hello {
  font-family: "Fraunces", serif;
  font-size: clamp(2rem, 5vw, 2.7rem);
  font-weight: 700;
  margin: 0.35rem 0 0.45rem 0;
}

.hint {
  font-size: 0.9rem;
  color: var(--muted);
  margin-top: 1.75rem;
}

.stButton > button {
  border-radius: 12px !important;
  font-weight: 600 !important;
  padding: 0.55rem 1.1rem !important;
}

footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<p class="hero-brand">3D Reconstruction</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-line">'
    "Phase 1: type a message. The API answers with <strong>Hello World</strong>. "
    "Video upload and 3D output come in later modules."
    "</p>",
    unsafe_allow_html=True,
)

try:
    health = httpx.get(f"{API_URL}/health", timeout=5.0).json()
    api_ok = bool(health.get("ok"))
except Exception:
    api_ok = False

if not api_ok:
    st.error(
        "API is not reachable. In another terminal run:\n\n"
        "`uvicorn api.main:app --host 127.0.0.1 --port 8000`"
    )
    st.stop()

st.markdown(
    """
<div class="panel">
  <h3>Enter your text</h3>
  <p>Anything short is fine — we are proving UI ↔ API works.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.form("hello_form", clear_on_submit=False):
    user_text = st.text_input(
        "Your message",
        placeholder="Type something here…",
        max_chars=500,
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Send to API", type="primary", use_container_width=True)

if submitted:
    cleaned = (user_text or "").strip()
    if not cleaned:
        st.warning("Please enter some text before sending.")
    else:
        with st.spinner("Talking to the API…"):
            try:
                resp = httpx.post(
                    f"{API_URL}/v1/hello",
                    json={"text": cleaned},
                    timeout=15.0,
                )
                if resp.status_code >= 400:
                    st.error(resp.text)
                else:
                    st.session_state["last_hello"] = resp.json()
            except Exception as exc:
                st.error(f"Could not reach the API: {exc}")

data = st.session_state.get("last_hello")
if data:
    st.markdown(
        f"""
<div class="result-card">
  <div class="label">API response</div>
  <p class="hello">{data.get("message", "Hello World")}</p>
  <p style="color:#5a6d7a;margin:0;">You sent: <strong>{data.get("input", "")}</strong></p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption(data.get("note") or "")

st.markdown(
    f'<p class="hint">Phase 1 · UI + API · text only · {API_URL}</p>',
    unsafe_allow_html=True,
)
