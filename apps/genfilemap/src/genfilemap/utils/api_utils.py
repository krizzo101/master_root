"""
API utilities for GenFileMap.

This module provides utility functions for handling API operations.
"""

import os
from typing import Dict, Any
from genfilemap.config import get_config_value

def get_api_key(vendor: str, config: Dict[str, Any] = None) -> str:
    """
    Get API key for the specified vendor from environment variables or configuration.
    
    Args:
        vendor: The API vendor (e.g., 'openai', 'anthropic')
        config: Optional configuration dictionary
        
    Returns:
        str: The API key
    """
    # Default environment variable names by vendor
    env_vars = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'local': 'LOCAL_API_KEY'
    }
    
    # Get the environment variable name from config if available
    api_key_var = None
    if config:
        api_key_var = get_config_value(config, f"api.api_key_var", None)
        # Also check for direct API key in config
        api_key = get_config_value(config, "api.key", None)
        if api_key:
            return api_key
    
    # If no custom var specified, use the default for the vendor
    if not api_key_var and vendor in env_vars:
        api_key_var = env_vars[vendor]
    
    # Get the API key from environment
    api_key = os.environ.get(api_key_var)
    
    if not api_key:
        raise ValueError(f"API key not found. Please set the {api_key_var} environment variable.")
    
    return api_key 