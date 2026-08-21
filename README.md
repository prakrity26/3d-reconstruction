# 3d-reconstruction

Upload a video in Streamlit → get **both**:
- `scene.glb` — interactive 3D of that video’s space  
- `flythrough.mp4` — moving path through that 3D  

Read **[PRODUCT.md](PRODUCT.md)** for the user experience vs current GPU workaround.

## Run

```bash
git checkout feature/04-dual-outputs
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --host 127.0.0.1 --port 8000
streamlit run ui/app.py
```

## Branches

| Branch | What |
|--------|------|
| `feature/01-ui-api-hello` | Text Hello World |
| `feature/02-video-upload` | Video upload stub |
| `feature/03-model` | Model / Colab GLB |
| `feature/04-dual-outputs` | GLB **+** flythrough MP4 in the product UI |
