"""
Base API client for LLM providers.

This module defines the base APIClient class that all provider-specific clients must implement.
"""

from typing import Optional, Dict, Any, List


class APIClient:
    """Base class for API clients"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize stats dictionary to track API usage
        self.stats = {"api_calls": 0, "tokens_used": 0}

    async def generate_completion(
        self, system_message: str, user_message: str, model: str, max_tokens: int = None
    ) -> str:
        """Generate a completion - to be implemented by specific vendor clients"""
        raise NotImplementedError("Must be implemented by subclass")


# Factory function to create the appropriate API client
def create_api_client(
    vendor: str, api_key: str, config: Optional[Dict[str, Any]] = None
) -> APIClient:
    """Factory function to create the appropriate API client"""
    if vendor == "openai":
        from genfilemap.api.openai import OpenAIClient

        return OpenAIClient(api_key, config)
    # Add other vendors as needed
    raise ValueError(f"Unsupported vendor: {vendor}")
