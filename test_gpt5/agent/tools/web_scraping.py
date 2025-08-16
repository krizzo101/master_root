from typing import Any

import requests
from bs4 import BeautifulSoup


def web_scrape(args: dict[str, Any]) -> dict[str, Any]:
    url = str(args.get("url", "")).strip()
    if not url:
        return {"error": "missing url"}
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        text = soup.get_text("\n", strip=True)
        return {"title": title, "content": text[:20000]}
    except Exception as e:
        return {"error": str(e)}
