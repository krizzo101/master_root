# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"API Client Module for Genfilemap","description":"This module provides implementations for API clients for various LLM providers, including a factory function to create the appropriate client based on vendor and API key.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation string providing an overview of the API client module.","line_start":1,"line_end":4},{"name":"Imports","description":"Import statements for necessary components from the base module.","line_start":5,"line_end":6},{"name":"API Client Factory Function","description":"Definition of the factory function for creating API clients based on vendor and API key.","line_start":8,"line_end":12}],"key_elements":[{"name":"create_api_client","description":"Factory function to create the appropriate API client.","line":12},{"name":"APIClient","description":"Class representing the API client.","line":5},{"name":"create_api_client","description":"Function imported from the base module, aliased as _create.","line":14}]}
"""
# FILE_MAP_END

"""
API client module for genfilemap

This package contains API client implementations for different LLM providers.
"""

from genfilemap.api.base import APIClient, create_api_client

__all__ = ["APIClient", "create_api_client"]


# Factory function for creating the appropriate API client
def create_api_client(vendor: str, api_key: str):
    """Factory function to create the appropriate API client."""
    from genfilemap.api.base import create_api_client as _create

    return _create(vendor, api_key)
