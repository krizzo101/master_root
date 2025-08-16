# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Document Analysis CLI for Documentation Rule Generator","description":"This module provides a command-line interface for analyzing documentation files, extracting structured information, and processing documents with various options including validation and taxonomy generation.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"This section contains all the import statements required for the module.","line_start":3,"line_end":30},{"name":"Logging Configuration","description":"This section configures the logging settings for the application.","line_start":31,"line_end":39},{"name":"Argument Parsing","description":"This section defines the function to parse command line arguments.","line_start":40,"line_end":122},{"name":"Environment Setup","description":"This section defines the function to set up the environment based on parsed arguments.","line_start":123,"line_end":170},{"name":"Document Path Retrieval","description":"This section defines the function to retrieve document paths from the input directory.","line_start":171,"line_end":208},{"name":"Document Processing","description":"This section defines the function to process a single document and handle various operations.","line_start":209,"line_end":389},{"name":"Main Function","description":"This section defines the main entry point for the document analyzer.","line_start":390,"line_end":431}],"key_elements":[{"name":"parse_args","description":"Function to parse command line arguments for the CLI.","line":43},{"name":"setup_environment","description":"Function to set up the environment based on command line arguments.","line":125},{"name":"get_document_paths","description":"Function to retrieve all document paths from the specified input path.","line":171},{"name":"process_document","description":"Function to process a single document and handle its analysis.","line":209},{"name":"main","description":"Main entry point function for executing the document analysis.","line":390}]}
"""
# FILE_MAP_END

#!/usr/bin/env python3

"""
Document Analysis CLI for Documentation Rule Generator.

This module provides a command-line interface for analyzing documentation files.
"""

import os
import sys
import argparse
import logging
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path to allow relative imports when run as script
script_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.dirname(script_dir)
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

from docRuleGen.rules_engine.extractors import (
    ContentExtractor,
    LLMTaxonomyGenerator,
)
from docRuleGen.rules_engine.preprocessors import PreprocessorManager
from docRuleGen.rules_engine.transformers import TransformationManager
from docRuleGen.rules_engine.generators import GeneratorManager
from docRuleGen.rules_engine.connectors import LLMOrchestrator
from docRuleGen.rules_engine.utils.config_loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("doc_analyzer")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze documentation files and extract structured information."
    )

    parser.add_argument(
        "input_path", help="Path to a document file or directory of documents"
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for analysis results",
        default="./test_output",
    )

    parser.add_argument(
        "--format",
        "-f",
        help="Output format (json, md, rule, all)",
        choices=["json", "md", "rule", "all"],
        default="json",
    )

    parser.add_argument(
        "--llm", "-l", help="Use LLM for enhanced analysis", action="store_true"
    )

    parser.add_argument(
        "--taxonomy", "-t", help="Generate document taxonomy", action="store_true"
    )

    parser.add_argument(
        "--validate", "-v", help="Validate generated rules", action="store_true"
    )

    parser.add_argument(
        "--improve", "-i", help="Improve rules based on validation", action="store_true"
    )

    parser.add_argument(
        "--recursive", "-r", help="Process directories recursively", action="store_true"
    )

    parser.add_argument(
        "--model", "-m", help="LLM model to use (provider-specific)", default=None
    )

    parser.add_argument(
        "--provider",
        "-p",
        help="LLM provider (openai, anthropic)",
        choices=["openai", "anthropic"],
        default=None,
    )

    parser.add_argument(
        "--config", "-c", help="Path to configuration file", default=None
    )

    parser.add_argument("--verbose", help="Enable verbose logging", action="store_true")

    return parser.parse_args()


def setup_environment(args):
    """Set up the environment based on arguments."""
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load configuration
    config = None
    if args.config:
        try:
            with open(args.config, "r") as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
    else:
        # Load default configuration
        config = load_config("app_config", "app_config")
        logger.info("Loaded default configuration")

    # Override config with command line arguments if specified
    if config is None:
        config = {}

    if args.provider:
        if "llm" not in config:
            config["llm"] = {}
        config["llm"]["default_provider"] = args.provider

    if args.model:
        if "llm" not in config:
            config["llm"] = {}
        if args.provider:
            config["llm"][f"default_{args.provider}_model"] = args.model
        else:
            default_provider = config.get("llm", {}).get("default_provider", "openai")
            config["llm"][f"default_{default_provider}_model"] = args.model

    return config


def get_document_paths(input_path: str, recursive: bool = False) -> List[str]:
    """
    Get all document paths from input path.

    Args:
        input_path: Path to a document file or directory
        recursive: Whether to process directories recursively

    Returns:
        List of document file paths
    """
    input_path = Path(input_path)

    if input_path.is_file():
        return [str(input_path)]

    if input_path.is_dir():
        document_paths = []

        # Define file extensions to process
        extensions = [".md", ".txt", ".rst", ".docx", ".pdf", ".html"]

        # Walk through directory
        if recursive:
            for root, _, files in os.walk(input_path):
                for file in files:
                    file_path = Path(root) / file
                    if any(file_path.suffix.lower() == ext for ext in extensions):
                        document_paths.append(str(file_path))
        else:
            for ext in extensions:
                document_paths.extend([str(f) for f in input_path.glob(f"*{ext}")])

        return sorted(document_paths)

    return []


def process_document(
    document_path: str,
    output_dir: str,
    format_type: str,
    config: Dict[str, Any],
    use_llm: bool = False,
    generate_taxonomy: bool = False,
    validate_rules: bool = False,
    improve_rules: bool = False,
) -> Dict[str, Any]:
    """
    Process a single document.

    Args:
        document_path: Path to the document file
        output_dir: Output directory
        format_type: Output format (json, md, rule, all)
        config: Configuration dictionary
        use_llm: Whether to use LLM for enhanced analysis
        generate_taxonomy: Whether to generate document taxonomy
        validate_rules: Whether to validate generated rules
        improve_rules: Whether to improve rules based on validation

    Returns:
        Dictionary with processing results
    """
    logger.info(f"Processing document: {document_path}")

    try:
        # Initialize components
        content_extractor = ContentExtractor()
        preprocessor = PreprocessorManager(config)
        transformation_manager = TransformationManager(config)
        generator = GeneratorManager(config)

        # Initialize LLM components if needed
        llm_orchestrator = None
        taxonomy_generator = None
        if use_llm or generate_taxonomy or validate_rules or improve_rules:
            llm_orchestrator = LLMOrchestrator(config)
            taxonomy_generator = LLMTaxonomyGenerator(config)

        # Extract content
        extracted_content = content_extractor.extract(document_path)
        if not extracted_content or (
            isinstance(extracted_content, dict) and "error" in extracted_content
        ):
            error_msg = (
                extracted_content.get("error", "Unknown error in content extraction")
                if isinstance(extracted_content, dict)
                else "Failed to extract document content"
            )
            logger.error(f"Content extraction failed: {error_msg}")
            return {"error": error_msg}

        # Add timestamp
        extracted_content["timestamp"] = datetime.datetime.now().isoformat()

        # Save raw content if format is json or all
        if format_type in ["json", "all"]:
            output_filename = f"{Path(document_path).stem}_analysis.json"
            output_path = Path(output_dir) / output_filename

            with open(output_path, "w") as f:
                json.dump(extracted_content, f, indent=2)

            logger.info(f"Saved raw content to {output_path}")

        # Process with preprocessors
        preprocessed_content = preprocessor.preprocess(extracted_content)

        # Generate taxonomy if requested
        taxonomy = None
        if generate_taxonomy and taxonomy_generator:
            logger.info(f"Generating taxonomy for {document_path}")
            taxonomy = taxonomy_generator.generate_taxonomy(document_path)

            if taxonomy and "error" not in taxonomy:
                # Save taxonomy
                output_filename = f"{Path(document_path).stem}_taxonomy.json"
                output_path = Path(output_dir) / output_filename

                with open(output_path, "w") as f:
                    json.dump(taxonomy, f, indent=2)

                logger.info(f"Saved taxonomy to {output_path}")

        # Transform content to rule format
        transformed_content = transformation_manager.transform(
            preprocessed_content,
            taxonomy=taxonomy,
            use_llm=use_llm,
            llm_orchestrator=llm_orchestrator,
        )

        # Generate rule files if format is rule or all
        rule_paths = []
        if format_type in ["rule", "all"]:
            # Determine output path
            rule_dir = Path(output_dir) / "rules"
            rule_dir.mkdir(parents=True, exist_ok=True)

            try:
                # Generate the rule
                rule_info = generator.generate(transformed_content, rule_dir)

                if rule_info and "path" in rule_info:
                    rule_path = rule_info["path"]
                    rule_paths.append(rule_path)
                    logger.info(f"Generated rule file: {rule_path}")
                elif rule_info and "error" in rule_info:
                    logger.error(f"Rule generation failed: {rule_info['error']}")
                    # If generated with error, try to fix the error and save anyway
                    if "content" in rule_info:
                        error_path = (
                            Path(rule_dir) / f"{Path(document_path).stem}_error.mdc"
                        )
                        with open(error_path, "w") as f:
                            if isinstance(rule_info["content"], (dict, list)):
                                # Handle case where content is a dictionary or list
                                json.dump(rule_info["content"], f, indent=2)
                            else:
                                f.write(str(rule_info["content"]))
                        logger.info(f"Saved error rule content to {error_path}")
                        rule_paths.append(str(error_path))
            except Exception as e:
                logger.error(f"Unexpected error in rule generation: {str(e)}")
                # Try to extract partial content and save it
                try:
                    error_path = (
                        Path(rule_dir) / f"{Path(document_path).stem}_error.mdc"
                    )
                    with open(error_path, "w") as f:
                        f.write(
                            f'---\nerror: "{str(e)}"\n---\n\n{json.dumps(transformed_content, indent=2)}'
                        )
                    logger.info(f"Saved error information to {error_path}")
                    rule_paths.append(str(error_path))
                except Exception as inner_e:
                    logger.error(f"Failed to save error information: {str(inner_e)}")

        # Validate and improve rules if requested
        if validate_rules and llm_orchestrator and rule_paths:
            for rule_path in rule_paths:
                # Read rule content
                with open(rule_path, "r") as f:
                    rule_content = f.read()

                # Validate rule
                logger.info(f"Validating rule: {rule_path}")
                validation_result = llm_orchestrator.validate_rule(
                    rule_content, rule_path
                )

                # Save validation result
                validation_filename = f"{Path(rule_path).stem}_validation.json"
                validation_path = Path(output_dir) / "validations" / validation_filename
                validation_path.parent.mkdir(parents=True, exist_ok=True)

                with open(validation_path, "w") as f:
                    json.dump(validation_result, f, indent=2)

                logger.info(f"Saved validation result to {validation_path}")

                # Improve rule if requested and validation failed
                if improve_rules:
                    if validation_result.get("status") == "fail":
                        logger.info(f"Improving rule: {rule_path}")

                        # Improve rule
                        improved_result = llm_orchestrator.improve_rule(
                            rule_content, validation_result
                        )

                        if improved_result and "content" in improved_result:
                            # Write improved rule
                            improved_path = str(rule_path).replace(
                                ".mdc", "_improved.mdc"
                            )

                            with open(improved_path, "w") as f:
                                f.write(improved_result["content"])

                            logger.info(f"Saved improved rule to {improved_path}")
                    else:
                        logger.info("Rule passed validation. No improvement needed.")

        return {
            "status": "success",
            "document_path": document_path,
            "output_dir": str(Path(output_dir)),
            "has_taxonomy": taxonomy is not None,
        }

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return {"error": f"Error processing document: {str(e)}"}


def main():
    """Main entry point for the document analyzer."""
    # Parse command line arguments
    args = parse_args()

    # Set up environment
    config = setup_environment(args)

    # Get document paths
    document_paths = get_document_paths(args.input_path, args.recursive)

    if not document_paths:
        logger.error(f"No documents found at {args.input_path}")
        return 1

    logger.info(f"Found {len(document_paths)} document(s) to process")

    # Process each document
    results = []
    for document_path in document_paths:
        result = process_document(
            document_path=document_path,
            output_dir=args.output,
            format_type=args.format,
            config=config,
            use_llm=args.llm,
            generate_taxonomy=args.taxonomy,
            validate_rules=args.validate,
            improve_rules=args.improve,
        )
        results.append(result)

    # Summarize results
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = len(results) - success_count

    logger.info(
        f"Processing complete. {success_count} document(s) processed successfully, {error_count} error(s)."
    )

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
