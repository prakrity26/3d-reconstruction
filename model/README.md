# Model module

## Outputs (both required for the product)

1. **`scene.glb`** — interactive 3D reconstruction of the uploaded video’s space  
2. **`flythrough.mp4`** — camera-path video through that reconstruction  

## User-facing flow (goal)

Streamlit upload → processing → both files available in the same UI.

## GPU

Heavy inference uses **VGGT** (`facebook/VGGT-1B` on Hugging Face) on a GPU.
On Mac, use the Colab notebook until an automatic GPU worker exists.

Notebook: `notebooks/colab_vggt_video_to_glb.ipynb`
