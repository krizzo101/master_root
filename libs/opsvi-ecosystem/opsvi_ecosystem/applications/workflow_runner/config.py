import logging
import os

import yaml


class Config:
    def __init__(self, config_path=None):
        self.config_path = config_path
        self.data = self._load_config()
        self._setup_logging()

    def _load_config(self):
        if not self.config_path:
            return {}
        if not os.path.exists(self.config_path):
            logging.warning(
                f"Config file not found: {self.config_path}. Using default config."
            )
            return {}
        with open(self.config_path) as f:
            if self.config_path.endswith(".yaml") or self.config_path.endswith(".yml"):
                return yaml.safe_load(f)
            else:
                return f.read()

    def _setup_logging(self):
        log_path = self.data.get("log_file", "workflow_runner.log")
        log_level = self.data.get("log_level", "DEBUG").upper()
        logging.basicConfig(
            filename=log_path,
            level=getattr(logging, log_level, logging.DEBUG),
            format="%(asctime)s %(levelname)s %(message)s",
        )
        logging.debug("Logging initialized.")
