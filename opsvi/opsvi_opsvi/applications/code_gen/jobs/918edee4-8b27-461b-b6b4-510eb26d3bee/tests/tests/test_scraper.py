import pytest
from unittest import mock
from simple_news_scraper.scraper import NewsScraper


def test_news_scraper_init_sets_attributes_correctly():
    url = "https://news.site"
    timeout = 5
    selectors = {"headline": "h1.title"}
    scraper = NewsScraper(url, timeout, selectors)
    assert scraper.url == url
    assert scraper.timeout == timeout
    assert scraper.selectors == selectors


def test_fetch_html_returns_html_content_successfully(monkeypatch):
    expected_html = "<html><head></head><body>Content</body></html>"

    class DummyResponse:
        status_code = 200
        text = expected_html

        def raise_for_status(self):
            pass

    def dummy_get(url, timeout):
        return DummyResponse()

    scraper = NewsScraper("https://dummyurl.com", 3, {})
    monkeypatch.setattr("requests.get", dummy_get)
    html = scraper.fetch_html()
    assert html == expected_html


import requests


def test_fetch_html_raises_exception_on_http_error(monkeypatch):
    def dummy_get(url, timeout):
        response = mock.Mock()
        response.status_code = 404
        response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        return response

    scraper = NewsScraper("https://dummyurl.com", 3, {})
    monkeypatch.setattr("requests.get", dummy_get)
    with pytest.raises(requests.HTTPError):
        scraper.fetch_html()


def test_fetch_headlines_returns_expected_list(monkeypatch):
    expected_headlines = ["News 1", "News 2"]

    class DummyParser:
        def extract_headlines(self, html, url, selectors):
            return expected_headlines

    scraper = NewsScraper("https://dummy.com", 3, {"headline": ".title"})

    # Patch fetch_html to return dummy HTML
    monkeypatch.setattr(scraper, "fetch_html", lambda: "<html></html>")

    # Patch HeadlineParser instance
    monkeypatch.setattr(
        "simple_news_scraper.scraper.HeadlineParser", lambda: DummyParser()
    )

    headlines = scraper.fetch_headlines()
    assert headlines == expected_headlines
