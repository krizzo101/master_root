# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Rule Generation CLI Tool","description":"This script provides a command-line interface for generating rules from documentation.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules and libraries for the script.","line_start":6,"line_end":18},{"name":"Logging Configuration","description":"Configures logging for the application.","line_start":20,"line_end":24},{"name":"Function Definitions","description":"Contains all function definitions used in the script.","line_start":26,"line_end":360}],"key_elements":[{"name":"parse_arguments","description":"Parses command-line arguments for the script.","line":27},{"name":"extract_content","description":"Extracts content from the source document.","line":94},{"name":"preprocess_content","description":"Preprocesses the extracted content.","line":119},{"name":"generate_rule","description":"Generates a rule from the preprocessed content.","line":144},{"name":"validate_rule","description":"Validates a generated rule and optionally improves it.","line":208},{"name":"main","description":"Main function that orchestrates the rule generation process.","line":278}]}
"""
# FILE_MAP_END

#!/usr/bin/env python3
"""
Rule Generation CLI Tool.

This script provides a command-line interface for generating rules from documentation.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any

from rules_engine.extractors import ExtractionManager
from rules_engine.preprocessors import PreprocessorManager
from rules_engine.utils.config_loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate rules from documentation files."
    )

    parser.add_argument("--source", required=True, help="Source document path")

    parser.add_argument("--rule-id", required=True, help="Rule ID (e.g., 301)")

    parser.add_argument(
        "--rule-name", required=True, help="Rule name (e.g., python-formatting)"
    )

    parser.add_argument(
        "--rule-type",
        default="parent",
        choices=["parent", "child", "standalone"],
        help="Rule type (parent, child, standalone)",
    )

    parser.add_argument("--description", help="Rule description (used in frontmatter)")

    parser.add_argument("--output", help="Output directory for generated rule")

    parser.add_argument(
        "--validate", action="store_true", help="Validate the generated rule"
    )

    parser.add_argument(
        "--improve", action="store_true", help="Improve the rule if validation fails"
    )

    parser.add_argument(
        "--preprocess-only",
        action="store_true",
        help="Only preprocess the content, don't generate rule",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    return parser.parse_args()


def extract_content(source_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract content from the source document.

    Args:
        source_path: Path to the source document
        config: Configuration dictionary

    Returns:
        Extracted content
    """
    # Initialize extractor manager
    extraction_manager = ExtractionManager(config)

    # Extract content
    logger.info(f"Extracting content from {source_path}")
    extracted_content = extraction_manager.extract(source_path)

    if extracted_content.get("status") != "success":
        logger.error(
            f"Failed to extract content: {extracted_content.get('error', 'Unknown error')}"
        )
        return extracted_content

    logger.info(f"Successfully extracted content from {source_path}")
    return extracted_content


def preprocess_content(
    extracted_content: Dict[str, Any], config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Preprocess extracted content.

    Args:
        extracted_content: Extracted content
        config: Configuration dictionary

    Returns:
        Preprocessed content
    """
    # Initialize preprocessor manager
    preprocessor_manager = PreprocessorManager(config)

    # Preprocess content
    logger.info("Preprocessing extracted content")
    preprocessed_content = preprocessor_manager.preprocess(extracted_content)

    if preprocessed_content.get("status") != "success":
        logger.error(
            f"Failed to preprocess content: {preprocessed_content.get('error', 'Unknown error')}"
        )
        return preprocessed_content

    logger.info("Successfully preprocessed content")
    return preprocessed_content


def generate_rule(
    preprocessed_content: Dict[str, Any], args, config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a rule from preprocessed content.

    Args:
        preprocessed_content: Preprocessed content
        args: Command-line arguments
        config: Configuration dictionary

    Returns:
        Generated rule information
    """
    # Import here to avoid circular imports
    from rules_engine.transformers import TransformationManager
    from rules_engine.generators import GeneratorManager

    # Update metadata
    metadata = preprocessed_content.get("metadata", {})
    metadata["id"] = args.rule_id
    metadata["name"] = args.rule_name
    metadata["type"] = args.rule_type

    if args.rule_type == "child" and args.parent_rule:
        metadata["parent"] = args.parent_rule

    preprocessed_content["metadata"] = metadata

    # Determine output path
    output_path = args.output
    if not output_path:
        output_dir = config.get("generation", {}).get(
            "output_directory", "generated_rules"
        )
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"{args.rule_id}-{args.rule_name}.mdc"
        output_path = os.path.join(output_dir, output_filename)

    # Initialize transformation manager
    transformation_manager = TransformationManager(config)

    # Transform preprocessed content
    logger.info("Transforming preprocessed content")
    transformed_content = transformation_manager.transform(preprocessed_content)

    if transformed_content.get("status") != "success":
        logger.error(
            f"Failed to transform content: {transformed_content.get('error', 'Unknown error')}"
        )
        return transformed_content

    # Initialize generator manager
    generator_manager = GeneratorManager(config)

    # Generate rule
    logger.info(f"Generating rule to {output_path}")
    generated_rule = generator_manager.generate(transformed_content, output_path)

    if generated_rule.get("status") != "success":
        logger.error(
            f"Failed to generate rule: {generated_rule.get('error', 'Unknown error')}"
        )
        return generated_rule

    logger.info(f"Successfully generated rule to {output_path}")
    return {
        "status": "success",
        "output_path": output_path,
        "rule_type": args.rule_type,
    }


def validate_rule(
    rule_path: str, should_improve: bool, config: Dict[str, Any], verbose: bool = False
) -> Dict[str, Any]:
    """
    Validate a generated rule and optionally improve it.

    Args:
        rule_path: Path to the rule file
        should_improve: Whether to improve the rule if validation fails
        config: Configuration dictionary
        verbose: Whether to print verbose output

    Returns:
        Dictionary with validation results
    """
    if verbose:
        logger.info(f"Validating generated rule: {rule_path}")

    try:
        # Import validation manager
        from rules_engine.validators import ValidationManager

        # Create validation manager
        validator = ValidationManager(config)

        # Validate rule
        validation_result = validator.validate_rule(rule_path, verbose=verbose)

        # Print summary
        if verbose:
            if validation_result["passed"]:
                logger.info(
                    f"Rule passed validation with score: {validation_result['score']}/10"
                )
            else:
                logger.warning(
                    f"Rule failed validation with score: {validation_result['score']}/10"
                )
                for issue in validation_result.get("issues", []):
                    logger.warning(f"  • {issue}")

        # Improve rule if requested and needed
        if should_improve and not validation_result["passed"]:
            if verbose:
                logger.info("Improving rule based on validation feedback...")

            # Improve rule
            improved_content = validator.improve_rule(
                rule_path, validation_result, verbose=verbose
            )

            # Save improved rule (overwrite original)
            with open(rule_path, "w", encoding="utf-8") as f:
                f.write(improved_content)

            if verbose:
                logger.info(f"Improved rule saved to: {rule_path}")

            # Re-validate improved rule
            validation_result = validator.validate_rule(rule_path, verbose=verbose)
            validation_result["improved"] = True

            if verbose:
                if validation_result["passed"]:
                    logger.info(
                        f"Improved rule passed validation with score: {validation_result['score']}/10"
                    )
                else:
                    logger.warning(
                        f"Improved rule failed validation with score: {validation_result['score']}/10"
                    )

        return validation_result

    except Exception as e:
        logger.error(f"Error validating rule: {str(e)}")
        return {
            "status": "error",
            "message": f"Error validating rule: {str(e)}",
            "passed": False,
        }


def main():
    """Main function."""
    # Parse command line arguments
    args = parse_arguments()

    # Load configuration
    app_config = load_config("app_config", "app_config")

    try:
        # Extract content from source document
        extracted_content = extract_content(args.source, app_config)
        if args.preprocess_only:
            # Preprocess content only
            preprocessed_content = preprocess_content(extracted_content, app_config)

            # Save preprocessed content
            output_dir = app_config.get("generation", {}).get(
                "output_directory", "generated_rules"
            )
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(
                output_dir, f"{args.rule_id}-{args.rule_name}.preprocessed.json"
            )

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(preprocessed_content, f, indent=2)

            logger.info(f"Preprocessed content saved to: {output_path}")

            # Add metadata for future processing
            preprocessed_content["metadata"] = {
                "id": args.rule_id,
                "name": args.rule_name,
                "type": args.rule_type,
                "description": args.description,
            }

            return 0
        else:
            # Preprocess content
            preprocessed_content = preprocess_content(extracted_content, app_config)

            # Add metadata for generation
            preprocessed_content["metadata"] = {
                "id": args.rule_id,
                "name": args.rule_name,
                "type": args.rule_type,
                "description": args.description,
            }

            # Generate rule
            logger.info("Transforming preprocessed content")
            from rules_engine.transformers import TransformationManager

            transformation_manager = TransformationManager()
            transformed_content = transformation_manager.transform(preprocessed_content)

            generation_result = generate_rule(transformed_content, args, app_config)

            if generation_result["status"] == "success":
                rule_path = generation_result["output_path"]
                logger.info(f"Rule generated successfully: {rule_path}")

                # Validate and improve rule if configured
                auto_validate = app_config.get("generation", {}).get(
                    "auto_validate", True
                )
                auto_improve = app_config.get("generation", {}).get(
                    "auto_improve", False
                )

                if auto_validate or args.validate:
                    validation_result = validate_rule(
                        rule_path,
                        should_improve=(auto_improve or args.improve),
                        config=app_config,
                        verbose=args.verbose,
                    )

                    if not validation_result["passed"]:
                        logger.warning(
                            "Validation failed. Check validation results for details."
                        )

                return 0
            else:
                logger.error(
                    f"Failed to generate rule: {generation_result.get('message', 'Unknown error')}"
                )
                return 1
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
