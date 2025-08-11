import pytest
from simple_news_scraper.parser import HeadlineParser


def test_headline_parser_init():
    parser = HeadlineParser()
    assert parser is not None


@pytest.mark.parametrize(
    "url, expected_domain",
    [
        ("https://www.bbc.com/news", "bbc.com"),
        ("http://subdomain.cnn.com/path", "cnn.com"),
        ("https://example.co.uk", "example.co.uk"),
        ("https://localhost:8000/page", "localhost"),
    ],
)
def test_get_domain_extracts_domain_correctly(url, expected_domain):
    domain = HeadlineParser.get_domain(url)
    assert domain == expected_domain


def test_get_selectors_for_url_returns_expected_selectors():
    parser = HeadlineParser()
    url = "https://bbc.com/news"
    selectors = parser.get_selectors_for_url(url, None)
    assert isinstance(selectors, dict)
    # Provide specific selectors
    custom_selectors = {"headline": ".custom-headline"}
    selectors = parser.get_selectors_for_url(url, custom_selectors)
    assert selectors == custom_selectors
    # Return default when selectors is None
    default_selectors = parser.get_selectors_for_url("https://unknownsite.com", None)
    assert isinstance(default_selectors, dict)


def test_extract_headlines_returns_list_and_handles_edge_cases():
    parser = HeadlineParser()
    html = """
    <html>
    <body>
    <h1 class="headline">Headline 1</h1>
    <h2 class="headline">Headline 2</h2>
    <div class="not-headline">Ignore Me</div>
    </body>
    </html>
    """
    selectors = {"headline": ".headline"}
    headlines = parser.extract_headlines(html, "https://bbc.com", selectors)
    assert isinstance(headlines, list)
    assert "Headline 1" in headlines
    assert "Headline 2" in headlines

    # Test with empty HTML
    empty_headlines = parser.extract_headlines("", "https://bbc.com", selectors)
    assert empty_headlines == []

    # Test with malformed HTML
    malformed_html = '<html><head><title>Test</title></head><body><h1 class="headline">Headline</body></html'
    headlines_malformed = parser.extract_headlines(
        malformed_html, "https://bbc.com", selectors
    )
    assert isinstance(headlines_malformed, list)
