# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Rule Validation and Improvement Utility","description":"This script validates rule files for structure and quality, and can optionally generate improved versions based on validation feedback.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules and packages for the script.","line_start":8,"line_end":17},{"name":"Logging Configuration","description":"Configures logging settings for the script.","line_start":19,"line_end":24},{"name":"Function: parse_arguments","description":"Parses command-line arguments for the script.","line_start":26,"line_end":41},{"name":"Function: validate_rule","description":"Validates a rule file and returns validation results.","line_start":63,"line_end":116},{"name":"Function: improve_rule","description":"Improves a rule based on validation feedback.","line_start":118,"line_end":152},{"name":"Function: save_results","description":"Saves validation results to a specified file.","line_start":153,"line_end":172},{"name":"Function: main","description":"Main entry point of the script that orchestrates the validation and improvement process.","line_start":175,"line_end":206}],"key_elements":[{"name":"parse_arguments","description":"Function to parse command-line arguments.","line":28},{"name":"validate_rule","description":"Function to validate a rule file.","line":63},{"name":"improve_rule","description":"Function to improve a rule based on validation feedback.","line":118},{"name":"save_results","description":"Function to save validation results to a file.","line":153},{"name":"main","description":"Main function that runs the script.","line":175},{"name":"logger","description":"Logger instance for logging messages.","line":25}]}
"""
# FILE_MAP_END

#!/usr/bin/env python3
"""
Command-line utility for validating and improving rule files.

This script validates rule files for structure and quality, and can optionally
generate improved versions based on validation feedback.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any

from rules_engine.validators import ValidationManager
from rules_engine.utils.config_loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Validate and improve rule files for structure and quality."
    )

    parser.add_argument("rule_path", help="Path to the rule file to validate")

    parser.add_argument(
        "--improve",
        action="store_true",
        help="Generate an improved version of the rule based on validation feedback",
    )

    parser.add_argument(
        "--output", help="Path to save validation results (JSON format)"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print verbose output"
    )

    return parser.parse_args()


def validate_rule(rule_path: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Validate a rule file.

    Args:
        rule_path: Path to the rule file
        verbose: Whether to print verbose output

    Returns:
        Dictionary with validation results
    """
    logger.info(f"Validating rule: {rule_path}")

    # Check if file exists
    if not os.path.exists(rule_path):
        logger.error(f"Rule file not found: {rule_path}")
        return {
            "status": "error",
            "message": f"Rule file not found: {rule_path}",
            "passed": False,
        }

    # Create ValidationManager
    try:
        validator = ValidationManager()

        # Validate rule
        validation_result = validator.validate_rule(rule_path, verbose=verbose)

        # Print summary
        if verbose:
            if validation_result["passed"]:
                print(
                    f"\n✅ Rule passed validation with score: {validation_result['score']}/10"
                )
            else:
                print(
                    f"\n❌ Rule failed validation with score: {validation_result['score']}/10"
                )
                if "issues" in validation_result and validation_result["issues"]:
                    print("\nStructural issues:")
                    for issue in validation_result["issues"]:
                        print(f"  • {issue}")

                if "feedback" in validation_result and validation_result["feedback"]:
                    print("\nQuality feedback:")
                    for category, feedback in validation_result["feedback"].items():
                        print(f"  • {category}: {feedback}")

        return validation_result

    except Exception as e:
        logger.error(f"Error validating rule: {str(e)}")
        return {
            "status": "error",
            "message": f"Error validating rule: {str(e)}",
            "passed": False,
        }


def improve_rule(
    rule_path: str, validation_result: Dict[str, Any], verbose: bool = False
) -> str:
    """
    Improve a rule based on validation feedback.

    Args:
        rule_path: Path to the rule file
        validation_result: Validation result from validate_rule
        verbose: Whether to print verbose output

    Returns:
        Path to the improved rule file
    """
    logger.info(f"Improving rule: {rule_path}")

    try:
        # Create ValidationManager
        validator = ValidationManager()

        # Improve rule
        improved_content = validator.improve_rule(
            rule_path, validation_result, verbose=verbose
        )

        # Save improved rule
        improved_path = rule_path + ".improved.md"
        with open(improved_path, "w", encoding="utf-8") as f:
            f.write(improved_content)

        if verbose:
            print(f"\n✅ Improved rule saved to: {improved_path}")

        return improved_path

    except Exception as e:
        logger.error(f"Error improving rule: {str(e)}")
        raise RuntimeError(f"Error improving rule: {str(e)}")


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save validation results to a file.

    Args:
        results: Validation results
        output_path: Path to save results
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Save results
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to: {output_path}")

    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        raise RuntimeError(f"Error saving results: {str(e)}")


def main():
    """
    Main entry point.
    """
    # Parse arguments
    args = parse_arguments()

    # Load config
    config = load_config("app_config", "app_config")

    try:
        # Validate rule
        validation_result = validate_rule(args.rule_path, verbose=args.verbose)

        # Improve rule if requested
        if args.improve:
            if not validation_result["passed"]:
                improved_path = improve_rule(
                    args.rule_path, validation_result, verbose=args.verbose
                )
                validation_result["improved_path"] = improved_path
            elif args.verbose:
                print("\nRule already meets quality standards. No improvement needed.")

        # Save results if output path provided
        if args.output:
            save_results(validation_result, args.output)

        # Return exit code based on validation result
        return 0 if validation_result["passed"] else 1

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
