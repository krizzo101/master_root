# tests/test_parser.py
import unittest

from scraper.parser import HeadlineExtractor

EXAMPLE_HTML = """<html><body>
<h3 class="headline">Alpha</h3>
<h3 class="headline">Beta</h3>
<h3 class="headline">Alpha</h3>
<a class="next" href="/news?page=2">Next</a>
</body></html>
"""

EXAMPLE_RULES = {"css_selectors": ["h3.headline"], "next_page_selector": "a.next"}


class TestHeadlineExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = HeadlineExtractor(EXAMPLE_RULES)

    def test_extract_headlines(self):
        headlines = self.extractor.extract_headlines(EXAMPLE_HTML)
        self.assertEqual(sorted(headlines), ["Alpha", "Beta"])

    def test_find_next_page_url(self):
        next_url = self.extractor.find_next_page_url(
            EXAMPLE_HTML, "https://example.com/news"
        )
        self.assertEqual(next_url, "https://example.com/news?page=2")

    def test_no_next_page(self):
        rules = {"css_selectors": ["h3.headline"]}
        no_nav_extract = HeadlineExtractor(rules)
        next_url = no_nav_extract.find_next_page_url(
            EXAMPLE_HTML, "https://example.com/news"
        )
        self.assertIsNone(next_url)


if __name__ == "__main__":
    unittest.main()
