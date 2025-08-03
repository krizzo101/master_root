"""
API client module for genfilemap

This package contains API client implementations for different LLM providers.
"""

from genfilemap.api.base import APIClient, create_api_client
from genfilemap.utils.api_utils import get_api_key
from typing import Optional, Dict, Any

__all__ = ["APIClient", "create_api_client", "get_api_key"]


# Factory function for creating the appropriate API client
def create_api_client(
    vendor: str, api_key: str, config: Optional[Dict[str, Any]] = None
):
    """Factory function to create the appropriate API client."""
    from genfilemap.api.base import create_api_client as _create

    return _create(vendor, api_key, config)
