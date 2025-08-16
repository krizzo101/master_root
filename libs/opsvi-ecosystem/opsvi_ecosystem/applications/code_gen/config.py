"""Configuration management for the code generation utility."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Application configuration."""

    # Server settings
    host: str = "0.0.0.0"
    # Use non-standard port by default to avoid conflicts
    port: int = 8010
    debug: bool = False

    # Logging
    log_level: str = "INFO"
    log_file: Path | None = None

    # OpenAI settings
    openai_api_key: str | None = None
    openai_model_o4_mini: str = "o4-mini"
    openai_model_gpt41: str = "gpt-4.1"
    openai_model_gpt41_mini: str = "gpt-4.1-mini"

    # Pipeline settings
    job_output_dir: Path = Path("jobs")
    max_concurrent_jobs: int = 5
    job_timeout_seconds: int = 300  # 5 minutes

    # Security settings
    rate_limit_requests: int = 10
    rate_limit_window: int = 60  # seconds
    max_request_size: int = 10000

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"

    # File settings
    max_file_size_mb: int = 100
    allowed_file_types: list[str] = None

    # Research settings
    enable_research: bool = True

    def __post_init__(self):
        """Initialize default values and validate configuration."""
        if self.allowed_file_types is None:
            self.allowed_file_types = [
                ".py",
                ".txt",
                ".md",
                ".json",
                ".csv",
                ".yml",
                ".yaml",
            ]

        # Ensure directories exist
        self.job_output_dir.mkdir(exist_ok=True)

        # Validate configuration
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values."""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port: {self.port}")

        if self.max_concurrent_jobs < 1:
            raise ValueError(
                f"max_concurrent_jobs must be >= 1: {self.max_concurrent_jobs}"
            )

        if self.job_timeout_seconds < 10:
            raise ValueError(
                f"job_timeout_seconds must be >= 10: {self.job_timeout_seconds}"
            )

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log_level: {self.log_level}")


def load_config() -> Config:
    """Load configuration from environment variables and defaults."""
    config = Config()

    # Server settings
    config.host = os.getenv("HOST", config.host)
    config.port = int(os.getenv("PORT", config.port))
    config.debug = os.getenv("DEBUG", "false").lower() == "true"

    # Logging
    config.log_level = os.getenv("LOG_LEVEL", config.log_level).upper()
    log_file_path = os.getenv("LOG_FILE")
    if log_file_path:
        config.log_file = Path(log_file_path)

    # OpenAI settings
    config.openai_api_key = os.getenv("OPENAI_API_KEY")
    config.openai_model_o4_mini = os.getenv(
        "OPENAI_MODEL_O4_MINI", config.openai_model_o4_mini
    )
    config.openai_model_gpt41 = os.getenv(
        "OPENAI_MODEL_GPT41", config.openai_model_gpt41
    )
    config.openai_model_gpt41_mini = os.getenv(
        "OPENAI_MODEL_GPT41_MINI", config.openai_model_gpt41_mini
    )

    # Pipeline settings
    job_dir = os.getenv("JOB_OUTPUT_DIR")
    if job_dir:
        config.job_output_dir = Path(job_dir)
        # Create directory if it doesn't exist
        config.job_output_dir.mkdir(parents=True, exist_ok=True)

    config.max_concurrent_jobs = int(
        os.getenv("MAX_CONCURRENT_JOBS", config.max_concurrent_jobs)
    )
    config.job_timeout_seconds = int(
        os.getenv("JOB_TIMEOUT_SECONDS", config.job_timeout_seconds)
    )

    # Security settings
    config.rate_limit_requests = int(
        os.getenv("RATE_LIMIT_REQUESTS", config.rate_limit_requests)
    )
    config.rate_limit_window = int(
        os.getenv("RATE_LIMIT_WINDOW", config.rate_limit_window)
    )
    config.max_request_size = int(
        os.getenv("MAX_REQUEST_SIZE", config.max_request_size)
    )

    # Redis
    config.redis_url = os.getenv("REDIS_URL", config.redis_url)

    # File settings
    config.max_file_size_mb = int(
        os.getenv("MAX_FILE_SIZE_MB", config.max_file_size_mb)
    )

    allowed_types = os.getenv("ALLOWED_FILE_TYPES")
    if allowed_types:
        config.allowed_file_types = [t.strip() for t in allowed_types.split(",")]

    # Research settings
    config.enable_research = os.getenv("ENABLE_RESEARCH", "true").lower() == "true"

    return config


def get_config() -> Config:
    """Get the global configuration instance."""
    if not hasattr(get_config, "_config"):
        get_config._config = load_config()
    return get_config._config


def reload_config() -> Config:
    """Reload configuration from environment."""
    if hasattr(get_config, "_config"):
        delattr(get_config, "_config")
    return get_config()


# Global configuration instance
config = get_config()
