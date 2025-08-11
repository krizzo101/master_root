# mypy: ignore-errors

import pytest

from src.adapters import playwright_scraper as ps


@pytest.mark.asyncio
async def test_scraper_offline(monkeypatch):
    # Patch internal Playwright usage to avoid real browser

    async def fake_scrape_page(url: str, wait_selector=None):  # noqa: D401
        return "Fake page content"

    monkeypatch.setattr(ps, "scrape_page", fake_scrape_page)

    text = await ps.scrape_page("https://example.com")
    assert text == "Fake page content"
