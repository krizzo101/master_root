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

    # Normalize Add File sections: ensure '+' prefix per line
    normalized_text = _normalize_patch_add_file_sections(patch_text)
    try:
        result = cookbook.process_patch(normalized_text, open_fn, write_fn, remove_fn)
        return str(result)
    except Exception as e:
        raise PatchApplyError(str(e)) from None


def _normalize_patch_add_file_sections(text: str) -> str:
    """Ensure every line in an '*** Add File:' section starts with '+'."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        if line.startswith("*** Add File: "):
            # Convert subsequent lines until next section marker
            while i < len(lines):
                nxt = lines[i]
                if nxt.startswith(
                    (
                        "*** End Patch",
                        "*** Update File:",
                        "*** Delete File:",
                        "*** Add File:",
                    )
                ):
                    break
                if not nxt.startswith("+"):
                    out.append("+" + nxt)
                else:
                    out.append(nxt)
                i += 1
            # Do not skip the marker line; loop will append it next
    return "\n".join(out)
