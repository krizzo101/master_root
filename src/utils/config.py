# mypy: ignore-errors
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = Field("sk-dummy-key-for-offline-mode", env="OPENAI_API_KEY")
    perplexity_api_key: str = Field("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", env="PERPLEXITY_API_KEY")
    qdrant_url: str = Field("http://localhost:6333", env="QDRANT_URL")
    qdrant_api_key: str | None = Field(None, env="QDRANT_API_KEY")
    model_embeddings: str = Field("text-embedding-3-large", env="EMBEDDING_MODEL")
    model_reasoning: str = Field("o4-mini", env="REASONING_MODEL")
    model_execution: str = Field("gpt-5-mini", env="EXECUTION_MODEL")

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
