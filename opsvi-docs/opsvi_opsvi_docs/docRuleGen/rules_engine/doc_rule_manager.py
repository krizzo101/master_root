# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Documentation Rule Manager","description":"Core module that coordinates rule generation by integrating path management, hierarchy management, and content generation","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":2,"line_end":17},{"name":"DocRuleManager Class","description":"Main class for rule generation coordination","line_start":19,"line_end":365},{"name":"Initialization","description":"Constructor and setup","line_start":26,"line_end":52},{"name":"Taxonomy Loading","description":"Loading taxonomy files","line_start":54,"line_end":69},{"name":"Rule Generation","description":"Main rule generation workflow","line_start":71,"line_end":258},{"name":"Report Generation","description":"Summary report creation","line_start":260,"line_end":365}],"key_elements":[{"name":"DocRuleManager.__init__","description":"Constructor initializing components","line":26},{"name":"DocRuleManager.load_taxonomy","description":"Load a taxonomy file","line":54},{"name":"DocRuleManager.generate_rules","description":"Main rule generation method","line":71},{"name":"generate_rule_worker","description":"Worker function for rule generation","line":94},{"name":"DocRuleManager.generate_summary_report","description":"Report generation method","line":260}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Documentation Rule Manager","description":"Core module that coordinates rule generation by integrating path management, hierarchy management, and content generation","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":1,"line_end":17},
# {"name":"DocRuleManager Class","description":"Main class for rule generation coordination","line_start":19,"line_end":365},
# {"name":"Initialization","description":"Constructor and setup","line_start":26,"line_end":52},
# {"name":"Taxonomy Loading","description":"Loading taxonomy files","line_start":54,"line_end":69},
# {"name":"Rule Generation","description":"Main rule generation workflow","line_start":71,"line_end":258},
# {"name":"Report Generation","description":"Summary report creation","line_start":260,"line_end":365}
# ],
# "key_elements":[
# {"name":"DocRuleManager.__init__","description":"Constructor initializing components","line":26},
# {"name":"DocRuleManager.generate_rules","description":"Main rule generation method","line":71},
# {"name":"generate_rule_worker","description":"Worker function for rule generation","line":94},
# {"name":"DocRuleManager.generate_summary_report","description":"Report generation method","line":260}
# ]
# }
# FILE_MAP_END

"""
Documentation Rule Manager Module for Documentation Rule Generator.

This module coordinates the generation of documentation rules by integrating
the path manager, hierarchy manager, and content generator components.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import time

# Import the specialized components
from .pathmanager.rule_paths import RulePathManager
from .hierarchymanager.rule_hierarchy import RuleHierarchyManager
from .contentgen.rule_content import RuleContentGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocRuleManager:
    """
    Coordinates the generation of documentation rules by integrating path management,
    hierarchy management, and content generation.
    """

    def __init__(
        self, doc_dir: str, output_dir: str = ".cursor/rules", max_workers: int = 4
    ):
        """
        Initialize the doc rule manager.

        Args:
            doc_dir: Base directory for documentation files
            output_dir: Directory to write rules to
            max_workers: Maximum number of parallel workers
        """
        self.doc_dir = Path(doc_dir)
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers

        # Create component instances
        self.path_manager = RulePathManager(output_dir)
        self.hierarchy_manager = RuleHierarchyManager(output_dir)
        self.content_generator = RuleContentGenerator(doc_dir)

        # Ensure the output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_taxonomy(self, taxonomy_file: str) -> Dict[str, Any]:
        """
        Load a taxonomy file.

        Args:
            taxonomy_file: Path to the taxonomy file

        Returns:
            Loaded taxonomy data
        """
        try:
            with open(taxonomy_file, "r", encoding="utf-8") as f:
                taxonomy = yaml.safe_load(f)
            return taxonomy
        except Exception as e:
            logger.error(f"Error loading taxonomy file: {str(e)}")
            return {}

    def generate_rules(self, taxonomy_file: str) -> List[Dict[str, Any]]:
        """
        Generate rules from a taxonomy file.

        Args:
            taxonomy_file: Path to the taxonomy file

        Returns:
            List of results for generated rules
        """
        # Load the taxonomy
        taxonomy = self.load_taxonomy(taxonomy_file)
        if not taxonomy:
            return [{"error": "Failed to load taxonomy"}]

        # Process all paths to determine the directory structure
        logger.info("Analyzing taxonomy and determining rule paths...")
        path_map = self.path_manager.process_taxonomy_paths(taxonomy)

        # Results will be collected here
        results = []

        # Define a worker function for parallel rule generation
        def generate_rule_worker(rule_data):
            try:
                rule_id = rule_data.get("id")
                rule_name = rule_data.get("name")
                source_files = rule_data.get("source_files", [])
                parent_id = rule_data.get("parent_id")
                category = rule_data.get("category", "Documentation")
                description = rule_data.get("description", "")

                # Skip rules without source files
                if not source_files:
                    logger.warning(
                        f"No source files specified for rule {rule_id}: {rule_name}"
                    )
                    return {
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "status": "skipped",
                        "reason": "No source files",
                    }

                # Get the path information for this rule
                if rule_id not in path_map:
                    logger.error(f"Rule {rule_id} not found in path map")
                    return {
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "status": "error",
                        "error": "Rule not found in path map",
                    }

                path_info = path_map[rule_id]
                full_path = path_info["full_path"]

                # Generate rule content
                content_result = self.content_generator.generate_rule_content(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    source_files=source_files,
                    category=category,
                    parent_id=parent_id,
                )

                if "error" in content_result:
                    return {
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "status": "error",
                        "error": content_result["error"],
                    }

                # Add description if provided in taxonomy
                if description and not content_result.get("description"):
                    content_result["description"] = description
                    if "frontmatter" in content_result:
                        content_result["frontmatter"]["description"] = description

                # Create the rule file
                success = self.content_generator.create_rule_file(
                    rule_content=content_result, full_path=full_path
                )

                if not success:
                    return {
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "status": "error",
                        "error": "Failed to create rule file",
                    }

                # Calculate line count
                line_count = 0
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        line_count = len(content.splitlines())
                except Exception as e:
                    logger.warning(
                        f"Error calculating line count for {rule_id}: {str(e)}"
                    )
                    line_count = 100  # Default

                return {
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "status": "success",
                    "file_path": str(full_path),
                    "relative_path": path_info["relative_path"],
                    "line_count": line_count,
                    "description": content_result.get("description", ""),
                    "parent_id": parent_id,
                    "level": path_info["level"],
                }

            except Exception as e:
                logger.error(f"Error generating rule {rule_data.get('id')}: {str(e)}")
                return {
                    "rule_id": rule_data.get("id", "unknown"),
                    "rule_name": rule_data.get("name", "unknown"),
                    "status": "error",
                    "error": str(e),
                }

        # Generate rules for each level of the hierarchy
        levels = {0: [], 1: [], 2: []}

        # Collect all rules by level
        for rule_id, path_info in path_map.items():
            level = path_info["level"]

            # Find the rule data in the taxonomy
            rule_data = None
            for category in taxonomy.get("categories", []):
                if rule_data:
                    break

                for parent_rule in category.get("rules", []):
                    if parent_rule.get("id") == rule_id:
                        rule_data = parent_rule.copy()
                        rule_data["category"] = category.get("name", "Documentation")
                        break

                    # Check child rules
                    for child_rule in parent_rule.get("child_rules", []):
                        if child_rule.get("id") == rule_id:
                            rule_data = child_rule.copy()
                            rule_data["category"] = category.get(
                                "name", "Documentation"
                            )
                            rule_data["parent_id"] = parent_rule.get("id")
                            break

                        # Check grandchild rules
                        for grandchild_rule in child_rule.get("child_rules", []):
                            if grandchild_rule.get("id") == rule_id:
                                rule_data = grandchild_rule.copy()
                                rule_data["category"] = category.get(
                                    "name", "Documentation"
                                )
                                rule_data["parent_id"] = child_rule.get("id")
                                break

            if rule_data:
                levels[level].append(rule_data)

        # Process each level sequentially
        for level in range(3):  # 0 = parent, 1 = child, 2 = grandchild
            level_rules = levels[level]
            if not level_rules:
                continue

            level_name = {0: "parent", 1: "child", 2: "grandchild"}[level]
            logger.info(f"Generating {len(level_rules)} {level_name} rules")

            # Use parallel processing if there's more than one rule at this level
            if len(level_rules) > 1 and self.max_workers > 1:
                with ThreadPoolExecutor(
                    max_workers=min(self.max_workers, len(level_rules))
                ) as executor:
                    level_results = list(
                        executor.map(generate_rule_worker, level_rules)
                    )
                    results.extend(level_results)
            else:
                # Process sequentially
                for rule_data in level_rules:
                    result = generate_rule_worker(rule_data)
                    results.append(result)

        # Now update all parent-child relationships
        logger.info("Updating parent-child relationships...")
        self.hierarchy_manager.update_all_parent_child_relationships(path_map)

        # Return the results
        return results

    def generate_summary_report(
        self,
        results: List[Dict[str, Any]],
        output_file: str = "rule_generation_report.md",
    ) -> None:
        """
        Generate a summary report of rule generation results.

        Args:
            results: List of rule generation results
            output_file: Path to the output report file
        """
        total_rules = len(results)
        successful_rules = sum(
            1 for result in results if result.get("status") == "success"
        )
        failed_rules = total_rules - successful_rules

        parent_rules = sum(
            1
            for result in results
            if result.get("level") == 0 and result.get("status") == "success"
        )
        child_rules = sum(
            1
            for result in results
            if result.get("level") in (1, 2) and result.get("status") == "success"
        )

        rules_over_200_lines = sum(
            1
            for result in results
            if result.get("status") == "success" and result.get("line_count", 0) > 200
        )

        # Generate the report content
        report = f"# Documentation Rule Generation Report\n\n"
        report += f"Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"## Summary\n\n"
        report += f"- **Total Rules**: {total_rules}\n"
        report += f"- **Successful**: {successful_rules} ({successful_rules/total_rules*100:.2f}%)\n"
        report += (
            f"- **Failed**: {failed_rules} ({failed_rules/total_rules*100:.2f}%)\n"
        )
        report += f"- **Parent Rules**: {parent_rules}\n"
        report += f"- **Child Rules**: {child_rules}\n"

        if rules_over_200_lines > 0:
            report += f"- **Warning**: {rules_over_200_lines} rules exceed 200 lines\n"

        # Group rules by parent ID for better organization
        parent_child_map = {}
        for result in results:
            if result.get("status") != "success":
                continue

            parent_id = result.get("parent_id")
            if parent_id:
                if parent_id not in parent_child_map:
                    parent_child_map[parent_id] = []
                parent_child_map[parent_id].append(result)

        # Add details for each parent rule and its children
        report += f"\n## Generated Rules\n\n"

        for result in sorted(
            [
                r
                for r in results
                if r.get("status") == "success" and not r.get("parent_id")
            ],
            key=lambda x: x.get("rule_id", ""),
        ):
            rule_id = result.get("rule_id", "Unknown")
            rule_name = result.get("rule_name", "Unknown")
            rule_path = result.get("relative_path", "Unknown")
            rule_line_count = result.get("line_count", "N/A")

            report += f"### {rule_id}: {rule_name}\n\n"
            report += f"Path: `{rule_path}` ({rule_line_count} lines)\n\n"

            # List child rules
            if rule_id in parent_child_map:
                report += "Child rules:\n\n"
                for child in sorted(
                    parent_child_map[rule_id], key=lambda x: x.get("rule_id", "")
                ):
                    child_id = child.get("rule_id", "Unknown")
                    child_name = child.get("rule_name", "Unknown")
                    child_path = child.get("relative_path", "Unknown")
                    child_line_count = child.get("line_count", "N/A")

                    report += f"- **{child_id}**: {child_name} - `{child_path}` ({child_line_count} lines)\n"

                report += "\n"

        # Add failed rules section if there are any
        if failed_rules > 0:
            report += "\n## Failed Rules\n\n"
            report += "| Rule ID | Rule Name | Error |\n"
            report += "|---------|-----------|-------|\n"

            for result in sorted(
                [r for r in results if r.get("status") != "success"],
                key=lambda x: x.get("rule_id", ""),
            ):
                rule_id = result.get("rule_id", "Unknown")
                rule_name = result.get("rule_name", "Unknown")
                error = result.get("error", "Unknown error")
                report += f"| {rule_id} | {rule_name} | {error} |\n"

        # Write the report to a file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"Report generated: {output_file}")

        # Also log a simple summary to console
        logger.info(
            f"Generated {successful_rules} of {total_rules} rules successfully ({successful_rules/total_rules*100:.2f}%)"
        )
        logger.info(
            f"Created {parent_rules} parent rules and {child_rules} child rules"
        )
        if rules_over_200_lines > 0:
            logger.warning(
                f"{rules_over_200_lines} rules exceed 200 lines and might need splitting"
            )
