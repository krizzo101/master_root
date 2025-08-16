# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Base API Client for LLM Providers","description":"This module defines the base APIClient class that all provider-specific clients must implement.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary typing utilities and the OpenAIClient for vendor-specific implementation.","line_start":3,"line_end":5},{"name":"APIClient Class","description":"Defines the base API client class for LLM providers.","line_start":6,"line_end":15},{"name":"Factory Function","description":"Factory function to create the appropriate API client based on the vendor.","line_start":16,"line_end":24}],"key_elements":[{"name":"APIClient","description":"Base class for API clients.","line":9},{"name":"__init__","description":"Constructor for the APIClient class that initializes the API key.","line":11},{"name":"create_api_client","description":"Factory function to create the appropriate API client.","line":19},{"name":"OpenAIClient","description":"Class imported for creating OpenAI specific API client.","line":22}]}
"""
# FILE_MAP_END

"""
Base API client for LLM providers.

This module defines the base APIClient class that all provider-specific clients must implement.
"""

from typing import Optional, Dict, Any, List


class APIClient:
    """Base class for API clients"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_completion(
        self, system_message: str, user_message: str, model: str, max_tokens: int = None
    ) -> str:
        """Generate a completion - to be implemented by specific vendor clients"""
        raise NotImplementedError("Must be implemented by subclass")


# Factory function to create the appropriate API client
def create_api_client(vendor: str, api_key: str) -> APIClient:
    """Factory function to create the appropriate API client"""
    if vendor == "openai":
        from genfilemap.api.openai import OpenAIClient

        return OpenAIClient(api_key)
    # Add other vendors as needed
    raise ValueError(f"Unsupported vendor: {vendor}")
