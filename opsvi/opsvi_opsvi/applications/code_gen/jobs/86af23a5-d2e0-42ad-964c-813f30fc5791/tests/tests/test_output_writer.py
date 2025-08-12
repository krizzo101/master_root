# tests/test_output_writer.py
import csv
import json
import os
import unittest

from scraper.output_writer import write_headlines


class TestOutputWriter(unittest.TestCase):
    data = [
        {"url": "https://example.com", "headline": "Alpha"},
        {"url": "https://example.com", "headline": "Beta"},
    ]

    def test_write_csv(self):
        fname = "test_out.csv"
        write_headlines(self.data, fname, "csv")
        with open(fname, encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            rows = list(csv_reader)
            self.assertEqual(len(rows), 2)
        os.remove(fname)

    def test_write_json(self):
        fname = "test_out.json"
        write_headlines(self.data, fname, "json")
        with open(fname, encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, self.data)
        os.remove(fname)

    def test_write_txt(self):
        fname = "test_out.txt"
        write_headlines(self.data, fname, "txt")
        with open(fname, encoding="utf-8") as f:
            lines = f.readlines()
        self.assertIn("[https://example.com] Alpha\n", lines)
        os.remove(fname)


if __name__ == "__main__":
    unittest.main()
