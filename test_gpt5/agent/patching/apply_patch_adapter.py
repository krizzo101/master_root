from __future__ import annotations

# Import the reference implementation
from importlib import import_module
from pathlib import Path


class PatchApplyError(Exception):
    pass


def apply_patch_text(repo_root: str, patch_text: str) -> str:
    """Apply a cookbook-style patch to repo_root using safe read/write.

    - Only relative paths are allowed by the reference implementation.
    - Writes create parent directories as needed.
    """
    repo = Path(repo_root)
    if not repo.exists():
        raise PatchApplyError(f"repo_root not found: {repo_root}")

    try:
        mod = import_module(
            "openai_cookbook_apply_patch_proxy"
        )  # optional alias if user vendors
    except Exception:
        mod = None

    if mod is None:
        # Load from .reference path directly
        ref_path = Path(
            "/home/opsvi/master_root/.reference/openai-cookbook/examples/gpt-5"
        )
        if not ref_path.joinpath("apply_patch.py").exists():
            raise PatchApplyError("reference apply_patch.py not found")
        import sys

        if str(ref_path) not in sys.path:
            sys.path.insert(0, str(ref_path))
        import apply_patch as cookbook
    else:
        cookbook = mod

    def open_fn(rel_path: str) -> str:
        return (repo / rel_path).read_text()

    def write_fn(rel_path: str, content: str) -> None:
        p = repo / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def remove_fn(rel_path: str) -> None:
        p = repo / rel_path
        if p.exists():
            p.unlink()

    try:
        result = cookbook.process_patch(patch_text, open_fn, write_fn, remove_fn)
        return str(result)
    except Exception as e:
        raise PatchApplyError(str(e)) from None
