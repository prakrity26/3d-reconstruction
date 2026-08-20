# 3d-reconstruction

Modular internship project: video → 3D GLB.

| Module | Status |
|--------|--------|
| UI | Live |
| API | Live |
| Database | Placeholder (`jobs/` on disk for now) |
| Queuing | Placeholder (thread stub) |
| **Model** | **Live via Google Colab + Hugging Face VGGT** |

## Why Colab?

Apple Silicon has no NVIDIA CUDA. VGGT needs a GPU, so inference runs on **Google Colab** using weights from **`facebook/VGGT-1B`** on Hugging Face. The app stores the video and serves the GLB.

## Branches

| Branch | Contents |
|--------|----------|
| `feature/01-ui-api-hello` | Text Hello World |
| `feature/02-video-upload` | Video upload + Hello World |
| `feature/03-model` | Video → Colab VGGT → GLB |

## Run

```bash
cd ~/3d-reconstruction
git checkout feature/03-model
source .venv/bin/activate
pip install -r requirements.txt

uvicorn api.main:app --host 127.0.0.1 --port 8000
streamlit run ui/app.py
```

## Model steps

1. Upload video in the UI
2. Open `notebooks/colab_vggt_video_to_glb.ipynb` in Colab (**GPU**)
3. Upload the same video → download `scene.glb`
4. Attach GLB in the UI → download 3D

## API

```http
POST /v1/jobs
GET  /v1/jobs/{id}
GET  /v1/jobs/{id}/video
POST /v1/jobs/{id}/glb
GET  /v1/jobs/{id}/glb
```
