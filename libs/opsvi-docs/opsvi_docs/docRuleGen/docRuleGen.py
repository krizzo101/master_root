# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Documentation Rule Generator Main Module","description":"Main entry point for the DocRuleGen application that converts documentation standards into Cursor Rules","last_updated":"2023-03-10","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":1,"line_end":13},{"name":"Environment Check","description":"Function to check required environment variables","line_start":16,"line_end":30},{"name":"Main Function","description":"Main entry point with argument parsing and execution","line_start":33,"line_end":121}],"key_elements":[{"name":"check_environment","description":"Function to verify environment setup","line":16},{"name":"main","description":"Main entry point function","line":33},{"name":"DocRuleManager initialization","description":"Creation of rule manager instance","line":83}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Documentation Rule Generator Main Module","description":"Main entry point for the DocRuleGen application that converts documentation standards into Cursor Rules","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":1,"line_end":13},
# {"name":"Environment Check","description":"Function to check required environment variables","line_start":16,"line_end":30},
# {"name":"Main Function","description":"Main entry point with argument parsing and execution","line_start":33,"line_end":121}
# ],
# "key_elements":[
# {"name":"check_environment","description":"Function to verify environment setup","line":16},
# {"name":"main","description":"Main entry point function","line":33},
# {"name":"DocRuleManager initialization","description":"Creation of rule manager instance","line":83}
# ]
# }
# FILE_MAP_END

#!/usr/bin/env python3
"""
Documentation Rule Generator

A specialized tool to generate Cursor Rules from documentation standards.
This tool extracts content from documentation files, transforms it into
rule format, and generates rule files with proper structure.
"""

import os
import sys
import argparse
import logging

# Import the rule manager
from rules_engine.doc_rule_manager import DocRuleManager

# Configure logging - default level, will be updated based on verbose flag
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_environment() -> bool:
    """
    Check if the required environment variables and directories exist.

    Returns:
        True if the environment is properly set up, False otherwise
    """
    # Check for OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY environment variable not set")
        return False

    # In a real application, we would check for other requirements here
    return True


def main():
    """
    Main entry point for the documentation rule generator.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate Cursor Rules from documentation standards."
    )
    parser.add_argument(
        "--taxonomy",
        default="taxonomy/enhanced_documentation_rules_taxonomy.yml",
        help="Path to the taxonomy YAML file",
    )
    parser.add_argument(
        "--doc-dir",
        default="doc_standards/",
        help="Path to the documentation directory",
    )
    parser.add_argument(
        "--output-dir",
        default=".cursor/rules",
        help="Directory to write the generated rules to",
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Maximum number of parallel workers"
    )
    parser.add_argument(
        "--report",
        default="rule_generation_report.md",
        help="Path to the output report file",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose debug logging"
    )

    args = parser.parse_args()

    # Update logging level if verbose flag is set
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Check environment
    if not check_environment():
        logger.error("Environment check failed")
        return 1

    # Create the rule manager
    rule_manager = DocRuleManager(
        doc_dir=args.doc_dir, output_dir=args.output_dir, max_workers=args.workers
    )

    # Generate the rules
    results = rule_manager.generate_rules(taxonomy_file=args.taxonomy)

    # Generate summary report
    rule_manager.generate_summary_report(results, args.report)

    # Print summary to console
    successful_rules = sum(1 for result in results if result.get("status") == "success")
    total_rules = len(results)

    print("\nRule generation completed!")
    print(f"Generated {successful_rules} of {total_rules} rules successfully")
    print(f"Success rate: {successful_rules/total_rules*100:.2f}%")
    print(f"Check {args.report} for details")

    return 0


if __name__ == "__main__":
    sys.exit(main())
