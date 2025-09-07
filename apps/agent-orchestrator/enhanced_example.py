#!/usr/bin/env python3
"""
Enhanced Error Handling Example
Demonstrates Python error handling best practices based on research summary
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging for proper error tracking
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataProcessingError(Exception):
    """Custom exception for data processing errors"""

    pass


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""

    pass


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file
    Demonstrates specific exception catching and EAFP principle
    """
    config_file = Path(config_path)

    # EAFP: Try to read the file rather than checking existence first
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
            logger.info(f"Successfully loaded config from {config_path}")
            return config

    except FileNotFoundError as e:
        # Specific exception handling with context
        logger.error(f"Configuration file not found: {config_path}")
        raise ConfigurationError(f"Missing config file: {config_path}") from e

    except json.JSONDecodeError as e:
        # Handle specific JSON parsing errors
        logger.error(f"Invalid JSON in config file: {e}")
        raise ConfigurationError(f"Invalid JSON format in {config_path}: {e}") from e

    except PermissionError as e:
        # Handle permission issues separately
        logger.error(f"Permission denied accessing config: {config_path}")
        raise ConfigurationError(f"Cannot access config file: {config_path}") from e


def process_data(data: Dict[str, Any], required_fields: list) -> Dict[str, Any]:
    """
    Process data with validation
    Demonstrates focused try blocks and proper error propagation
    """
    processed = {}

    for field in required_fields:
        # EAFP: Try to access the field rather than checking existence
        try:
            value = data[field]

            # Focused try block for specific operation
            try:
                # Example processing: convert strings to uppercase
                if isinstance(value, str):
                    processed[field] = value.upper()
                else:
                    processed[field] = value

            except AttributeError as e:
                # Specific error handling for processing
                logger.warning(f"Cannot process field '{field}': {e}")
                processed[field] = value  # Keep original value

        except KeyError as e:
            # Add context to the error
            error_msg = f"Required field '{field}' is missing from data"
            logger.error(error_msg)
            raise DataProcessingError(error_msg) from e

    logger.info(f"Successfully processed {len(processed)} fields")
    return processed


def divide_numbers(numerator: float, denominator: float) -> Optional[float]:
    """
    Safe division with proper error handling
    Demonstrates when to handle vs propagate errors
    """
    try:
        result = numerator / denominator
        return result

    except ZeroDivisionError:
        # Log the error with context
        logger.warning(f"Division by zero attempted: {numerator} / {denominator}")
        # Return None for recoverable error (business logic decision)
        return None

    except TypeError as e:
        # Non-recoverable error - propagate with context
        logger.error(
            f"Invalid types for division: {type(numerator)}, {type(denominator)}"
        )
        raise DataProcessingError(
            f"Cannot divide {type(numerator).__name__} by {type(denominator).__name__}"
        ) from e


def main():
    """
    Main application with top-level exception handler
    Demonstrates strategic error handling at application level
    """
    try:
        # Example 1: Load configuration (may fail)
        print("\n=== Configuration Loading Example ===")
        try:
            config = load_config("config.json")
            print(f"Config loaded: {config}")
        except ConfigurationError as e:
            print(f"Using default config due to: {e}")
            config = {"default": True, "timeout": 30}

        # Example 2: Process data with required fields
        print("\n=== Data Processing Example ===")
        sample_data = {"name": "example", "value": 42, "description": "test data"}

        try:
            processed = process_data(sample_data, ["name", "value", "description"])
            print(f"Processed data: {processed}")
        except DataProcessingError as e:
            logger.error(f"Failed to process data: {e}")
            print(f"Data processing failed: {e}")

        # Example 3: Try with missing field (will fail gracefully)
        print("\n=== Missing Field Example ===")
        try:
            processed = process_data(sample_data, ["name", "missing_field"])
        except DataProcessingError as e:
            print(f"Expected error handled: {e}")

        # Example 4: Safe division
        print("\n=== Division Examples ===")
        result = divide_numbers(10, 2)
        print(f"10 / 2 = {result}")

        result = divide_numbers(10, 0)
        print(f"10 / 0 = {result} (handled gracefully)")

        # Example 5: This would raise an error (uncomment to test)
        # result = divide_numbers("10", 2)  # Type error - will propagate

    except Exception as e:
        # Top-level handler for any unhandled exceptions
        logger.critical(f"Unexpected application error: {e}", exc_info=True)
        print(f"\nApplication error: {e}")
        print("Please check the logs for details")
        return 1

    print("\n=== Application completed successfully ===")
    return 0


if __name__ == "__main__":
    exit(main())
