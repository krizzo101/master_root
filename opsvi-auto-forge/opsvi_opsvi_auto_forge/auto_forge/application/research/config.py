"""Configuration management for the research stack."""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from .errors import ConfigError
from .models import ClientConfig, ResearchConfig


@lru_cache(maxsize=1)
def load_mcp_config() -> Dict[str, Any]:
    """Load MCP configuration from mcp.json with caching."""
    config_path = Path("/home/opsvi/auto_forge/mcp.json")

    if not config_path.exists():
        # Return default configuration
        return {
            "brave": {
                "enabled": True,
                "timeout": 30.0,
                "max_results": 10,
                "api_key": os.getenv("BRAVE_API_KEY"),
            },
            "firecrawl": {
                "enabled": True,
                "timeout": 30.0,
                "max_results": 10,
                "api_key": os.getenv("FIRECRAWL_API_KEY"),
            },
            "arxiv": {
                "enabled": True,
                "timeout": 30.0,
                "max_results": 10,
            },
            "context7": {
                "enabled": True,
                "timeout": 30.0,
                "max_results": 10,
                "api_key": os.getenv("CONTEXT7_API_KEY"),
            },
            "sequential_thinking": {
                "enabled": True,
                "timeout": 60.0,
                "max_results": 1,
            },
            "default_timeout": 30.0,
            "max_parallel_requests": 5,
            "enable_synthesis": True,
            "enable_persistence": True,
            "synthesis_model": "gpt-4",
        }

    try:
        with open(config_path) as f:
            config = json.load(f)

        # Validate required fields
        required_clients = [
            "brave",
            "firecrawl",
            "arxiv",
            "context7",
            "sequential_thinking",
        ]
        for client in required_clients:
            if client not in config:
                config[client] = {
                    "enabled": True,
                    "timeout": 30.0,
                    "max_results": 10,
                }

        return config

    except (OSError, json.JSONDecodeError) as e:
        raise ConfigError(f"Failed to load MCP configuration: {e}")


def get_research_config() -> ResearchConfig:
    """Get the complete research configuration."""
    raw_config = load_mcp_config()

    # Build client configurations
    clients = {}
    for client_name, client_config in raw_config.items():
        if client_name in [
            "brave",
            "firecrawl",
            "arxiv",
            "context7",
            "sequential_thinking",
        ]:
            clients[client_name] = ClientConfig(
                name=client_name,
                enabled=client_config.get("enabled", True),
                timeout=client_config.get("timeout", 30.0),
                max_results=client_config.get("max_results", 10),
                api_key=client_config.get("api_key"),
                metadata=client_config.get("metadata", {}),
            )

    return ResearchConfig(
        clients=clients,
        default_timeout=raw_config.get("default_timeout", 30.0),
        max_parallel_requests=raw_config.get("max_parallel_requests", 5),
        enable_synthesis=raw_config.get("enable_synthesis", True),
        enable_persistence=raw_config.get("enable_persistence", True),
        synthesis_model=raw_config.get("synthesis_model", "gpt-4"),
        metadata=raw_config.get("metadata", {}),
    )


def get_client_config(client_name: str) -> ClientConfig | None:
    """Get configuration for a specific client."""
    config = get_research_config()
    return config.clients.get(client_name)


def validate_config() -> bool:
    """Validate the configuration and return True if valid."""
    try:
        config = get_research_config()

        # Check that at least one client is enabled
        enabled_clients = [c for c in config.clients.values() if c.enabled]
        if not enabled_clients:
            raise ConfigError("No clients are enabled in configuration")

        # Validate timeouts
        for client in config.clients.values():
            if client.timeout <= 0:
                raise ConfigError(
                    f"Invalid timeout for client {client.name}: {client.timeout}"
                )
            if client.max_results <= 0:
                raise ConfigError(
                    f"Invalid max_results for client {client.name}: {client.max_results}"
                )

        return True

    except Exception as e:
        raise ConfigError(f"Configuration validation failed: {e}")


def clear_config_cache() -> None:
    """Clear the configuration cache."""
    load_mcp_config.cache_clear()
