from typing import Any

import requests


def web_search(args: dict[str, Any]) -> dict[str, Any]:
    """Very simple web search via DuckDuckGo HTML (no API key)."""
    query = str(args.get("query", "")).strip()
    if "limit" not in args:
        return {"error": "missing required parameter: limit"}
    try:
        max_results = int(args.get("limit", 3))
    except Exception:
        return {"error": "limit must be an integer"}
    if not query:
        return {"results": [], "note": "empty query"}
    try:
        r = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            timeout=15,
        )
        r.raise_for_status()
        # crude extraction
        results: list[dict[str, str]] = []
        for line in r.text.splitlines():
            if "result__a" in line and 'href="' in line:
                try:
                    href = line.split('href="')[1].split('"')[0]
                    title = line.split(">", 1)[1].split("<", 1)[0]
                except Exception:
                    continue
                results.append({"title": title, "url": href})
                if len(results) >= max_results:
                    break
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}
