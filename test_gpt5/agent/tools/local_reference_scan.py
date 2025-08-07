from __future__ import annotations

import os
from typing import Any


def local_reference_scan(args: dict[str, Any]) -> dict[str, Any]:
    if "root" not in args:
        return {"error": "missing required parameter: root"}
    root = str(args.get("root", "")).strip()
    query = str(args.get("query", "")).strip()
    max_files = int(args.get("max_files", 20))
    max_bytes = int(args.get("max_bytes", 20000))
    if not query:
        return {"results": []}
    results: list[dict[str, Any]] = []
    try:
        for dirpath, _, filenames in os.walk(root):
            for fname in filenames:
                path = os.path.join(dirpath, fname)
                try:
                    with open(path, "rb") as f:
                        data = f.read(max_bytes)
                    text = data.decode(errors="ignore")
                    if query.lower() in text.lower():
                        results.append({"path": path, "snippet": text[:500]})
                        if len(results) >= max_files:
                            return {"results": results}
                except Exception:
                    continue
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}
