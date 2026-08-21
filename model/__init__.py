"""Model module — video → GLB + flythrough MP4."""

from model.backend import (
    attach_flythrough,
    attach_glb,
    describe_backend,
    flythrough_path,
    glb_path,
    jobs_dir,
)

__all__ = [
    "attach_flythrough",
    "attach_glb",
    "describe_backend",
    "flythrough_path",
    "glb_path",
    "jobs_dir",
]
