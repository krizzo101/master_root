import sys

import pytest
from simple_news_scraper import __main__


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    # Patch sys.argv during tests and reset after
    original_argv = sys.argv.copy()
    yield
    sys.argv = original_argv


def test_parse_args_with_no_args_uses_default_url(monkeypatch):
    monkeypatch.setattr("sys.argv", ["script_name"])
    args = __main__.parse_args()
    assert args.url == __main__.DEFAULT_URL
    assert isinstance(args.url, str)


def test_parse_args_with_custom_url(monkeypatch):
    test_url = "https://example.com"
    monkeypatch.setattr("sys.argv", ["script_name", test_url])
    args = __main__.parse_args()
    assert args.url == test_url


def test_main_runs_and_calls_fetch_headlines_and_print(monkeypatch):
    class DummyScraper:
        def __init__(self, url, timeout, selectors):
            self.url = url
            self.timeout = timeout
            self.selectors = selectors

        def fetch_headlines(self):
            return ["Headline 1", "Headline 2"]

    monkeypatch.setattr(__main__, "NewsScraper", DummyScraper)
    monkeypatch.setattr(__main__, "HeadlineParser", lambda: None)

    printed = {}

    def fake_print_headlines(headlines):
        printed["headlines"] = headlines

    monkeypatch.setattr(__main__, "print_headlines", fake_print_headlines)
    monkeypatch.setattr(__main__, "load_config", lambda x: {})
    monkeypatch.setattr(__main__, "setup_logging", lambda level: None)
    monkeypatch.setattr(
        "simple_news_scraper.__main__.parse_args",
        lambda: type("Args", (), {"url": "https://news.com"})(),
    )

    __main__.main()
    assert "headlines" in printed
    assert len(printed["headlines"]) == 2
