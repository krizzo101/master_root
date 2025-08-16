# scraper/output_writer.py
"""
Result Output Writer:
Serializes headlines into structured UTF-8 encoded output files (CSV, JSON, or text).
"""
import csv
import json
from typing import List, Dict
import logging

logger = logging.getLogger("scraper.output_writer")


def write_headlines(
    headline_data: List[Dict[str, str]], filename: str, fmt: str = "csv"
) -> None:
    """
    Write headlines to an output file in the specified format (csv, json, txt).
    Args:
        headline_data (List[Dict[str, str]]): List of dicts with keys: 'url', 'headline'.
        filename (str): Output filename.
        fmt (str): 'csv', 'json', or 'txt'.
    Raises:
        ValueError: If output format is unsupported.
    """
    try:
        if fmt == "csv":
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["url", "headline"])
                writer.writeheader()
                writer.writerows(headline_data)
        elif fmt == "json":
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(headline_data, f, ensure_ascii=False, indent=2)
        elif fmt == "txt":
            with open(filename, "w", encoding="utf-8") as f:
                for item in headline_data:
                    f.write(f"[{item['url']}] {item['headline']}\n")
        else:
            raise ValueError(f"Unsupported output format: {fmt}")
        logger.info(f"Headlines written to {filename} as {fmt}")
    except Exception as e:
        logger.error(f"Failed to write output file {filename}: {e}")
        raise e
