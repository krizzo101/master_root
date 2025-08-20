"""Application settings and configuration management."""

from typing import Dict, List, Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "Autonomous Software Factory"
    app_version: str = "0.1.0"
    debug: bool = True  # Changed to True for better debugging
    log_level: str = "DEBUG"  # Changed to DEBUG for comprehensive logging

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: List[str] = ["*"]

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    redis_connection_timeout: int = 5

    # Neo4j
    neo4j_url: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")
    neo4j_max_connection_lifetime: int = 3600
    neo4j_max_connection_pool_size: int = 50

    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: List[str] = ["json"]
    celery_task_acks_late: bool = True
    celery_worker_prefetch_multiplier: int = 1
    celery_task_routes: Dict[str, Dict[str, str]] = {
        "workers.tasks.heavy.*": {"queue": "heavy"},
        "workers.tasks.io.*": {"queue": "io"},
        "workers.tasks.test.*": {"queue": "test"},
    }

    # AI Models
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.1

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_max_tokens: int = 4000
    anthropic_temperature: float = 0.1

    # Vector Store
    vector_store_type: str = "chroma"  # chroma, qdrant, redis
    vector_store_url: Optional[str] = None
    vector_store_collection: str = "auto_forge"

    # Prometheus
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    require_auth: bool = Field(
        default=False, description="Require authentication for API endpoints"
    )

    # JWT Authentication
    jwt_secret_key: str = "your-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Testing
    test_coverage_minimum: float = 85.0
    test_timeout: int = 300

    # Quality Gates
    critic_overall_threshold: float = 0.95
    critic_policy_threshold: float = 0.90

    # Feature Flags
    enable_mcp: bool = False
    enable_vector_memory: bool = True
    enable_auto_repair: bool = True
    enable_performance_optimization: bool = True

    # Repair Configuration
    repair_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum repair attempts for validation failures",
    )

    # Decision Kernel & Retrieval Orchestrator
    reasoning_enable: bool = Field(default=False, description="Enable Decision Kernel")
    knowledge_enable: bool = Field(
        default=False, description="Enable Retrieval Orchestrator"
    )
    reasoning_verifier_model: str = Field(
        default="gpt-4.1-mini", description="Model for verification"
    )
    reasoning_min_confidence: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )

    @field_validator("celery_broker_url", "celery_result_backend", mode="before")
    @classmethod
    def set_celery_urls(cls, v: Optional[str], info) -> str:
        """Set Celery URLs to Redis URL if not provided."""
        if v is None:
            return info.data.get("redis_url", "redis://localhost:6379/0")
        return v

    @field_validator("vector_store_url", mode="before")
    @classmethod
    def set_vector_store_url(cls, v: Optional[str], info) -> str:
        """Set vector store URL based on type."""
        if v is None:
            if info.data.get("vector_store_type") == "redis":
                return info.data.get("redis_url", "redis://localhost:6379/0")
            elif info.data.get("vector_store_type") == "chroma":
                return "http://localhost:8000"
            elif info.data.get("vector_store_type") == "qdrant":
                return "http://localhost:6333"
        return v or ""

    model_config = ConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


# Global settings instance
settings = Settings()
