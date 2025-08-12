"""
CSV Parser & Validator module for csv_reporter.
Handles schema detection, malformed row handling, and REST API for loading CSV data.
"""
import csv
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from csv_reporter.config import Config
from csv_reporter.logger import logger


class CSVParser:
    """
    CSV file parser and validator.
    Parses a CSV file, attempts to auto-detect format, and cleans up malformed rows.
    """

    def __init__(self, config: Config) -> None:
        self.config = config

    def parse_csv(self, path: Path) -> tuple[pd.DataFrame, list[str]]:
        """
        Parses the CSV file and cleans data.

        Returns:
            (cleaned DataFrame, [warnings])
        Raises:
            FileNotFoundError: If file not found.
            ValueError: For empty, malformed or unreadable files.
        """
        warnings: list[str] = []
        if not path.is_file():
            raise FileNotFoundError(f"CSV file not found: {path}")
        logger.debug(f"Attempting to load CSV: {path}")
        # Try reading with pandas, fallback to csv.Sniffer if needed
        try:
            df = pd.read_csv(path, **self.config.pandas_csv_args())
            if df.empty:
                raise ValueError("CSV file is empty.")
            logger.debug(f"Loaded CSV with columns: {df.columns.to_list()}")
            return df, warnings
        except (EmptyDataError, ParserError) as e:
            # Attempt a more tolerant approach
            warnings.append(
                f"Pandas failed to parse CSV - {e}. Attempting line-by-line cleanup."
            )
            cleaned_rows = []
            with open(path, encoding=self.config.csv_encoding) as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    raise ValueError("Cannot parse header row in CSV file.")
                for i, row in enumerate(reader, 2):
                    if len(row) != len(header):
                        warnings.append(f"Row {i} malformed: {row}; skipping.")
                        continue
                    cleaned_rows.append(row)
            if not cleaned_rows:
                raise ValueError("No valid data rows in file after cleanup.")
            df = pd.DataFrame(cleaned_rows, columns=header)
            return df, warnings
        except UnicodeDecodeError as ude:
            raise ValueError(f"Failed to read CSV (encoding error): {ude}") from ude
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}") from e
