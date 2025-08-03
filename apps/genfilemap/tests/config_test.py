#!/usr/bin/env python3
"""
Test script to verify configuration loading in genfilemap.
"""

import os
import sys
from genfilemap.config import load_config, get_config_value

def print_config_values():
    """Print key configuration values."""
    # Load default config
    print("Loading default configuration...")
    config = load_config()
    
    # Print model configuration
    model = get_config_value(config, "api.model")
    print(f"Default model from config: {model}")
    
    # Print other key configuration values
    vendor = get_config_value(config, "api.vendor")
    print(f"API vendor: {vendor}")
    
    # Check ignore file configuration
    ignore_file = get_config_value(config, "file_processing.ignore_file")
    print(f"Ignore file path: {ignore_file}")
    
    # Check if the ignore file exists
    if ignore_file:
        expanded_path = os.path.expanduser(ignore_file)
        print(f"Expanded ignore file path: {expanded_path}")
        if os.path.exists(expanded_path):
            print(f"Ignore file exists at: {expanded_path}")
        else:
            print(f"Ignore file DOES NOT exist at: {expanded_path}")

if __name__ == "__main__":
    print_config_values() 