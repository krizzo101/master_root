from __future__ import annotations

import py_compile
from pathlib import Path
from typing import Any


def run_tests(args: dict[str, Any]) -> dict[str, Any]:
    repo_root = Path(str(args.get("repo_root", ".")))
    if not repo_root.exists():
        return {"error": f"repo_root not found: {repo_root}"}
    errors: list[dict[str, str]] = []
    checked = 0
    for p in repo_root.rglob("*.py"):
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as e:
            errors.append({"file": str(p.relative_to(repo_root)), "error": str(e)})
        checked += 1
        if checked >= 500:
            break
    return {"checked": checked, "errors": errors, "ok": len(errors) == 0}
