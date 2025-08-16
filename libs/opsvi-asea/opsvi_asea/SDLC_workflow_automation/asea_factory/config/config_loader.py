import os
import yaml
from dotenv import load_dotenv


class ConfigLoader:
    def __init__(self, env_path=".env", config_path="config.yml"):
        load_dotenv(env_path)
        self.env = dict(os.environ)
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def get(self, key, default=None):
        return self.config.get(key, self.env.get(key, default))

    def get_env(self, key, default=None):
        return self.env.get(key, default)

    def get_config(self, key, default=None):
        return self.config.get(key, default)
