"""
Configuration management using Pydantic Settings.

This module provides centralized configuration management for the ACCF Research Agent,
supporting environment variables, .env files, and AWS Secrets Manager integration.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: Optional[str] = None
    neo4j_database: str = "neo4j"

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_embedding_model: str = "text-embedding-3-large"
    openai_model: str = "gpt-4o"

    # Application Configuration
    log_level: str = "INFO"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # AWS Configuration (for secrets management)
    aws_region: str = "us-east-1"
    aws_secrets_manager_enabled: bool = False

    # Security Configuration
    secret_key: Optional[str] = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Performance Configuration
    max_workers: int = 4
    request_timeout: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = "ACCF_"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
