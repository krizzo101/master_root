"""
Configuration management for csv_reporter.
Supports loading overrides via YAML config file.
"""
from pathlib import Path
from typing import Any

import yaml

_DEFAULTS = {
    "csv": {
        "encoding": "utf-8",
        "delimiter": ",",
    },
    "pandas": {
        "na_values": "",
        "keep_default_na": True,
    },
}


class Config:
    """
    Holds configuration for all modules, supports updates from YAML file.
    """

    def __init__(self) -> None:
        self._config = _DEFAULTS.copy()
        self.csv_encoding = self._config["csv"]["encoding"]
        self.csv_delimiter = self._config["csv"]["delimiter"]
        self._pandas_args = self._config["pandas"].copy()

    def load_from_file(self, path: Path) -> None:
        """
        Loads YAML config file, updates in-place.
        """
        with open(path, encoding="utf-8") as f:
            user_conf = yaml.safe_load(f)
            if not isinstance(user_conf, dict):
                raise ValueError(f"Invalid configuration format in {path}")
            self._recursive_update(self._config, user_conf)
        # Refresh per-section config
        self.csv_encoding = self._config["csv"].get("encoding", "utf-8")
        self.csv_delimiter = self._config["csv"].get("delimiter", ",")
        self._pandas_args = self._config["pandas"].copy()

    def pandas_csv_args(self) -> dict[str, Any]:
        """
        Returns pandas.read_csv compatible arguments, incorporating config overrides.
        """
        return {
            "encoding": self.csv_encoding,
            "delimiter": self.csv_delimiter,
            **self._pandas_args,
        }

    @staticmethod
    def _recursive_update(base: dict[str, Any], updates: dict[str, Any]) -> None:
        """
        Recursively update a dictionary in place with another dict.
        """
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                Config._recursive_update(base[key], value)
            else:
                base[key] = value

    def __repr__(self) -> str:
        return f"Config({self._config})"
