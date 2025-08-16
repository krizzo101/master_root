"""
Configuration for OpenAI Codex MCP Server
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class CodexConfig:
    """Configuration for OpenAI Codex integration"""

    # API Configuration
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    model: str = os.environ.get(
        "CODEX_MODEL", "gpt-4"
    )  # Default to GPT-4 as Codex is deprecated

    # Execution Configuration
    max_tokens: int = int(os.environ.get("CODEX_MAX_TOKENS", "2000"))
    temperature: float = float(os.environ.get("CODEX_TEMPERATURE", "0.7"))
    top_p: float = float(os.environ.get("CODEX_TOP_P", "1.0"))

    # Safety Configuration
    stop_sequences: list = None
    max_retries: int = int(os.environ.get("CODEX_MAX_RETRIES", "3"))
    timeout: int = int(os.environ.get("CODEX_TIMEOUT", "30"))

    # Output Configuration
    streaming: bool = os.environ.get("CODEX_STREAMING", "false").lower() == "true"
    format_output: bool = (
        os.environ.get("CODEX_FORMAT_OUTPUT", "true").lower() == "true"
    )

    # Context Management
    context_window: int = int(os.environ.get("CODEX_CONTEXT_WINDOW", "8000"))
    include_file_context: bool = (
        os.environ.get("CODEX_INCLUDE_CONTEXT", "true").lower() == "true"
    )

    # Cache Configuration
    enable_cache: bool = os.environ.get("CODEX_ENABLE_CACHE", "true").lower() == "true"
    cache_dir: str = os.environ.get("CODEX_CACHE_DIR", "/tmp/codex_cache")
    cache_ttl: int = int(os.environ.get("CODEX_CACHE_TTL", "3600"))  # seconds

    def __post_init__(self):
        """Validate configuration"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        if self.stop_sequences is None:
            self.stop_sequences = ["```", "\n\n\n"]

        # Create cache directory if needed
        if self.enable_cache:
            os.makedirs(self.cache_dir, exist_ok=True)
