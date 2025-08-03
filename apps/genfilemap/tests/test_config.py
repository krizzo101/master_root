#!/usr/bin/env python3
"""
Test script to debug configuration loading issues.
"""
import os
from genfilemap.config import load_config, get_config_value

def main():
    """Main test function"""
    # Load config
    config = load_config()
    
    # Print the configured min_lines setting - trying both formats
    nested_min_lines = config.get("file_processing", {}).get("min_lines", "NOT FOUND")
    flat_min_lines = get_config_value(config, "file_processing.min_lines", "NOT FOUND")
    direct_min_lines = get_config_value(config, "min_lines", "NOT FOUND")
    
    print(f"Config loaded from: {os.path.expanduser('~/.genfilemap/.config/config.json')}")
    print(f"Nested access min_lines: {nested_min_lines}")
    print(f"Flat access min_lines: {flat_min_lines}")
    print(f"Direct access min_lines: {direct_min_lines}")
    
    # Print entire config for debugging
    print("\nFull configuration:")
    import json
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    main() 