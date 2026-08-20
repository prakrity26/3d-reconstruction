"""Model module — video → 3D GLB (runs on Colab / GPU; local is the contract)."""

from model.backend import attach_glb, describe_backend, jobs_dir

__all__ = ["attach_glb", "describe_backend", "jobs_dir"]
