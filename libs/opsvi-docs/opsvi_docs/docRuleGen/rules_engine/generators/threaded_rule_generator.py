# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Threaded Rule Generator","description":"This module extends the enhanced_rule_generator with multi-threading support to generate multiple rules concurrently.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation for the threaded rule generator module.","line_start":2,"line_end":6},{"name":"Imports","description":"Import statements for required libraries and modules.","line_start":8,"line_end":14},{"name":"Logging Configuration","description":"Configuration for logging within the module.","line_start":16,"line_end":20},{"name":"Rule Worker Function","description":"Function to generate a single rule in a worker thread.","line_start":22,"line_end":40},{"name":"Threaded Rule Generation Function","description":"Function to generate multiple rules concurrently using threading.","line_start":42,"line_end":132}],"key_elements":[{"name":"_generate_rule_worker","description":"Worker function to generate a single rule.","line":24},{"name":"generate_rules_threaded","description":"Function to generate multiple rules from a taxonomy file concurrently.","line":50},{"name":"logger","description":"Logger instance for logging messages.","line":18},{"name":"create_and_verify_rule","description":"Function imported from enhanced_rule_generator to create and verify rules.","line":14}]}
"""
# FILE_MAP_END

"""
Threaded rule generator module for parallel generation of multiple rules.

This module extends the enhanced_rule_generator with multi-threading support
to generate multiple rules concurrently.
"""

import os
import yaml
import logging
import concurrent.futures
from typing import List, Dict, Any, Tuple

from rules_engine.generators.enhanced_rule_generator import create_and_verify_rule

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _generate_rule_worker(rule_data: Dict[str, str]) -> Tuple[str, str, str]:
    """
    Worker function to generate a single rule.

    Args:
        rule_data: Dictionary containing rule_id, rule_name, and category

    Returns:
        Tuple of (rule_id, rule_name, result) where result is the file path or error message
    """
    rule_id = rule_data["rule_id"]
    rule_name = rule_data["rule_name"]
    category = rule_data["category"]

    try:
        logger.info(f"Starting generation of Rule {rule_id}: {rule_name}")
        file_path = create_and_verify_rule(rule_id, rule_name, category)
        logger.info(f"Successfully generated Rule {rule_id}: {rule_name}")
        return (rule_id, rule_name, file_path)
    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(
            f"Failed to generate Rule {rule_id}: {rule_name} - {error_message}"
        )
        return (rule_id, rule_name, error_message)


def generate_rules_threaded(
    taxonomy_file: str, max_workers: int = 4, max_rules: int = None
) -> List[Dict[str, str]]:
    """
    Generate multiple rules from a taxonomy file concurrently using threading.

    Args:
        taxonomy_file: Path to the YAML taxonomy file
        max_workers: Maximum number of concurrent workers (threads)
        max_rules: Maximum number of rules to generate (for testing or limiting)

    Returns:
        List of dictionaries with generation results
    """
    logger.info(f"Loading taxonomy from: {taxonomy_file}")

    # Make sure the taxonomy file exists
    if not os.path.exists(taxonomy_file):
        raise FileNotFoundError(f"Taxonomy file not found: {taxonomy_file}")

    # Load the taxonomy
    with open(taxonomy_file, "r", encoding="utf-8") as f:
        taxonomy = yaml.safe_load(f)

    # Extract rules to generate
    rules_to_generate = []
    for category in taxonomy.get("categories", []):
        category_name = category.get("name", "Unknown")
        for rule in category.get("rules", []):
            rules_to_generate.append(
                {
                    "rule_id": rule.get("id", "000"),
                    "rule_name": rule.get("name", "Unknown Rule"),
                    "category": category_name,
                }
            )

    # Limit number of rules if specified
    if max_rules is not None and max_rules > 0:
        rules_to_generate = rules_to_generate[:max_rules]

    total_rules = len(rules_to_generate)
    logger.info(
        f"Preparing to generate {total_rules} rules using {max_workers} worker threads"
    )

    results = []

    # Use ThreadPoolExecutor to parallelize rule generation
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all rule generation tasks
        future_to_rule = {
            executor.submit(_generate_rule_worker, rule): rule
            for rule in rules_to_generate
        }

        # Process results as they complete
        for i, future in enumerate(concurrent.futures.as_completed(future_to_rule), 1):
            rule = future_to_rule[future]
            try:
                rule_id, rule_name, result = future.result()
                success = not result.startswith("Error")

                # Add result to the results list
                results.append(
                    {
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "success": success,
                        "result": result,
                    }
                )

                # Log progress
                logger.info(f"Progress: {i}/{total_rules} rules processed")

            except Exception as e:
                logger.error(
                    f"Exception while processing rule {rule['rule_id']}: {str(e)}"
                )
                results.append(
                    {
                        "rule_id": rule["rule_id"],
                        "rule_name": rule["rule_name"],
                        "success": False,
                        "result": f"Exception: {str(e)}",
                    }
                )

    # Log summary
    successful = sum(1 for r in results if r["success"])
    logger.info(
        f"Rule generation complete. Successfully generated {successful} of {total_rules} rules"
    )

    return results
