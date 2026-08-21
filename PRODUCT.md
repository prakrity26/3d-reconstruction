# Product goal

## Model choice
Use **LingBot-Map** for reconstruction quality (official internship model).
Colab notebook: `notebooks/colab_lingbot_video_to_glb.ipynb`

VGGT notebooks are experimental only.

# Product goal (what the user should experience)

## One sentence
Upload a video in Streamlit → see processing → download **both**:
1. **`scene.glb`** — interactive 3D of the places in that video (open in a 3D viewer / Blender)
2. **`flythrough.mp4`** — a moving camera video through that same 3D reconstruction

## What each file means

| Output | Type | What you get |
|--------|------|----------------|
| `scene.glb` | 3D model | Orbit / walk the reconstructed space from your video |
| `flythrough.mp4` | Video | A rendered path through that space (feels like a “3D video”) |

Your original upload is a normal 2D video. The model builds geometry from many frames. The GLB is the space; the flythrough is motion through that space.

## Ideal user flow (final product)

```text
Streamlit
  1. Upload video
  2. “Video is processing…”
  3. Download scene.glb
  4. Play / download flythrough.mp4
```

No Colab UI for the end user. GPU work happens in a backend worker.

## Current reality on a MacBook (M4)

No NVIDIA GPU → reconstruction still needs a cloud GPU (Colab) for now.
Until that worker is automated, developers run the Colab notebook, then attach
both files in Streamlit. The **UI contract is already “both outputs”**.

Next engineering steps: Database + Queuing + auto GPU worker so Colab disappears from the user path.
