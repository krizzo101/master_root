import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class Neo4jSettings(BaseSettings):
    uri: str = Field(..., env="NEO4J_URI")
    user: str = Field(..., env="NEO4J_USER")
    password: str = Field(..., env="NEO4J_PASSWORD")


class OpenAISettings(BaseSettings):
    api_key: str = Field(..., env="OPENAI_API_KEY")
    model: str = Field("gpt-4.1-mini", env="OPENAI_MODEL")


class PrometheusSettings(BaseSettings):
    enabled: bool = Field(True, env="PROMETHEUS_ENABLED")
    port: int = Field(9090, env="PROMETHEUS_PORT")


class BraveSettings(BaseSettings):
    api_key: str = Field(..., env="BRAVE_API_KEY")


class FirecrawlSettings(BaseSettings):
    api_key: str = Field(..., env="FIRECRAWL_API_KEY")


class Config(BaseSettings):
    neo4j: Neo4jSettings
    openai: OpenAISettings
    prometheus: PrometheusSettings
    brave: BraveSettings
    firecrawl: FirecrawlSettings

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @classmethod
    def from_yaml(cls, path: str):
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)


"""
Usage:
from src.applications.oamat.config import Config
config = Config.from_yaml("config/development/config.yaml")
# or just Config() to load from env
"""
