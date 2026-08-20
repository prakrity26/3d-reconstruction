# Model module

Turns an indoor / phone **video** into a **3D GLB** point cloud.

## Why Google Colab + Hugging Face?

Your MacBook (Apple Silicon) does not have NVIDIA CUDA.
The reconstruction model needs a GPU, so we run it on **Google Colab** and load weights from **Hugging Face** (`facebook/VGGT-1B`).

Local API/UI stay thin: they store the video, accept the GLB back, and let the user download it.

## Flow

```text
Streamlit UI  →  upload video
FastAPI       →  save jobs/<id>/input.*
You           →  open notebooks/colab_vggt_video_to_glb.ipynb on Colab (GPU)
Colab         →  VGGT from Hugging Face → scene.glb
Streamlit UI  →  upload scene.glb for that job
FastAPI       →  GET /v1/jobs/{id}/glb  (download 3D)
```

## CLI (optional, for when you have a GPU machine)

```bash
python -m model.cli --video path/to/clip.mp4 --out path/to/scene.glb
```

On a Mac without CUDA this prints instructions to use Colab instead.
