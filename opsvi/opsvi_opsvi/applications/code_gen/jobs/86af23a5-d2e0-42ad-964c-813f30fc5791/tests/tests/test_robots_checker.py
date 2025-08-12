# tests/test_robots_checker.py
import unittest
from unittest.mock import Mock, patch

from scraper.robots_checker import RobotsChecker


class TestRobotsChecker(unittest.TestCase):
    @patch("requests.get")
    def test_is_allowed_grants(self, mock_get):
        # allow everything
        mock_get.return_value = Mock(status_code=200, text="User-agent: *\nAllow: /\n")
        rc = RobotsChecker(user_agent="FakeBot")
        self.assertTrue(rc.is_allowed("https://example.com/news"))

    @patch("requests.get")
    def test_is_allowed_denies(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200, text="User-agent: *\nDisallow: /private\n"
        )
        rc = RobotsChecker(user_agent="FakeBot")
        self.assertFalse(rc.is_allowed("https://example.com/private"))

    @patch("requests.get")
    def test_robots_txt_not_found(self, mock_get):
        # If robots.txt is 404, assume disallow (conservative)
        mock_get.return_value = Mock(status_code=404)
        rc = RobotsChecker(user_agent="FakeBot")
        self.assertFalse(rc.is_allowed("https://example.com/any"))


if __name__ == "__main__":
    unittest.main()
