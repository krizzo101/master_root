from typing import Any

import requests


def tech_docs_search(args: dict[str, Any]) -> dict[str, Any]:
    """Fetch basic docs content from OpenAI Python README as a placeholder."""
    q = str(args.get("query", "responses create")).strip()
    try:
        url = "https://raw.githubusercontent.com/openai/openai-python/main/README.md"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        lines = r.text.splitlines()
        hits = [line for line in lines if q.lower() in line.lower()]
        return {"count": len(hits), "samples": hits[:20]}
    except Exception as e:
        return {"error": str(e)}
