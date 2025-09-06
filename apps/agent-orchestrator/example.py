#!/usr/bin/env python3
"""
Example script demonstrating proper error handling practices.
Based on research summary findings.
"""

import json
import sys
from pathlib import Path


def read_config_file(file_path):
    """Read and parse a JSON config file with specific error handling."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config file: {e}")
        return {}
    except PermissionError:
        print(f"Permission denied reading: {file_path}")
        return {}


def process_user_data(data):
    """Process user data with specific exception handling."""
    try:
        user_id = data["user_id"]
        age = int(data["age"])

        if age < 0:
            raise ValueError("Age cannot be negative")

        return {
            "id": user_id,
            "age": age,
            "category": "adult" if age >= 18 else "minor",
        }
    except KeyError as e:
        print(f"Missing required field: {e}")
        return None
    except ValueError as e:
        print(f"Invalid data format: {e}")
        return None


def write_results(data, output_path):
    """Write results with resource management and error handling."""
    try:
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Results written to {output_path}")
    except PermissionError:
        print(f"Permission denied writing to: {output_path}")
        raise
    except OSError as e:
        print(f"OS error writing file: {e}")
        raise


def main():
    """Main function demonstrating EAFP principle and error handling."""
    config_path = Path("config.json")
    output_path = Path("results.json")

    # Load configuration
    config = read_config_file(config_path)

    # Sample data to process
    test_data = [
        {"user_id": "user1", "age": "25"},
        {"user_id": "user2", "age": "17"},
        {"user_id": "user3", "age": "invalid"},
        {"missing_id": "test", "age": "30"},
    ]

    results = []

    # Process each data entry
    for data in test_data:
        processed = process_user_data(data)
        if processed:
            results.append(processed)

    # Write results if we have any
    if results:
        try:
            write_results(results, output_path)
        except (PermissionError, OSError):
            print("Failed to write results, exiting")
            sys.exit(1)
    else:
        print("No valid data to write")


if __name__ == "__main__":
    main()
