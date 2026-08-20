"""CLI entry for the model module.

Usage:
    python -m model.cli --video clip.mp4 --out scene.glb
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.backend import describe_backend


def main() -> None:
    parser = argparse.ArgumentParser(description="Video → 3D GLB (GPU / Colab)")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if not args.video.is_file():
        raise SystemExit(f"Video not found: {args.video}")

    info = describe_backend()
    print("Local CUDA reconstruction is not enabled on this machine.")
    print(f"Use Google Colab notebook: {info['notebook']}")
    print(f"Hugging Face weights:     {info['weights']}")
    print()
    print("Steps:")
    print("  1. Open the notebook in Google Colab (Runtime → GPU).")
    print(f"  2. Upload: {args.video}")
    print(f"  3. Download the GLB and save it as: {args.out}")
    print("  4. In the Streamlit UI, attach that GLB to your job.")
    raise SystemExit(2)


if __name__ == "__main__":
    main()
