"""
DataProcessor module: Handles aggregation, summary statistics, and data analysis.
"""
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from csv_reporter.config import Config
from csv_reporter.logger import logger


class DataProcessor:
    """
    Analyzes and summarizes input CSV data.
    Provides summary stats per column, such as count, mean, min/max for numerics,
    and count of unique values for categoricals.
    """

    def __init__(self, config: Config) -> None:
        self.config = config

    def process(
        self, df: pd.DataFrame, progress_cb: Callable[[int], None] | None = None
    ) -> dict[str, Any]:
        """
        Process data and return a summary suitable for reporting.

        Args:
            df: DataFrame to summarize.
            progress_cb: Optional callback for progress bar (receives current row number).
        Returns:
            dict summary, keyed by column name, value is dict of stats.
        Raises:
            ValueError: On failure to process.
        """
        logger.debug(f"Processing {len(df)} rows, {df.columns.tolist()} columns.")
        summary: dict[str, Any] = {}
        row_total = len(df)
        for idx, col in enumerate(df.columns):
            col_data = df[col]
            stats = {}
            num_values = pd.to_numeric(col_data, errors="coerce").dropna()
            # Numeric columns summary
            if num_values.shape[0] >= 1 and (
                num_values.dtype == float or num_values.dtype == int
            ):
                stats["type"] = "numeric"
                stats["count"] = num_values.shape[0]
                stats["mean"] = float(np.round(num_values.mean(), 4))
                stats["std"] = float(np.round(num_values.std(ddof=0), 4))
                stats["min"] = float(num_values.min())
                stats["max"] = float(num_values.max())
                stats["missing"] = int(row_total - num_values.shape[0])
            else:
                # Treat as categorical/text
                stats["type"] = "categorical"
                unique = col_data.dropna().unique()
                stats["unique_count"] = int(len(unique))
                stats["top"] = None
                if len(unique) > 0:
                    top_values = col_data.value_counts().head(3)
                    stats["top"] = [(k, int(v)) for k, v in top_values.items()]
                stats["missing"] = int(col_data.isnull().sum())
            summary[col] = stats
            if progress_cb:
                progress_cb(idx + 1)
        logger.debug(f"Data processing completed. Summary: {summary}")
        return summary
