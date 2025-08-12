# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Rule Hierarchy Manager","description":"This module provides functions for managing relationships between rules, including parent-child references and cross-references.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules for functionality.","line_start":3,"line_end":13},{"name":"Logging Configuration","description":"Configures logging for the module.","line_start":15,"line_end":17},{"name":"RuleHierarchyManager Class","description":"Class that manages hierarchical relationships between rules.","line_start":18,"line_end":201},{"name":"update_all_parent_child_relationships Method","description":"Updates all parent-child relationships based on a path map.","line_start":202,"line_end":276}],"key_elements":[{"name":"RuleHierarchyManager","description":"Class for managing hierarchical relationships between rules.","line":18},{"name":"__init__","description":"Constructor for initializing the RuleHierarchyManager.","line":24},{"name":"update_parent_with_children","description":"Updates a parent rule file with references to its child rules.","line":33},{"name":"update_all_parent_child_relationships","description":"Updates all parent-child relationships based on a path map.","line":202}]}
"""
# FILE_MAP_END

"""
Rule Hierarchy Manager Module for Documentation Rule Generator.

This module provides functions for managing relationships between rules,
including parent-child references and cross-references.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RuleHierarchyManager:
    """
    Manages hierarchical relationships between rules, including parent-child references
    and cross-references between related rules.
    """

    def __init__(self, output_dir: str = ".cursor/rules"):
        """
        Initialize the hierarchy manager.

        Args:
            output_dir: Base directory for rules output
        """
        self.output_dir = Path(output_dir)

    def update_parent_with_children(
        self, parent_path: Path, child_rules: List[Dict[str, Any]]
    ) -> bool:
        """
        Update a parent rule file with references to its child rules.

        Args:
            parent_path: Path to the parent rule file
            child_rules: List of child rule information

        Returns:
            True if successful, False otherwise
        """
        if not parent_path.exists():
            logger.error(f"Parent rule file not found: {parent_path}")
            return False

        try:
            # Read the parent rule file
            with open(parent_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract the frontmatter and JSON content
            parts = content.split("---", 2)
            if len(parts) < 3:
                logger.error(f"Invalid rule file format: {parent_path}")
                return False

            frontmatter = parts[1]
            json_content = parts[2].strip()

            # Parse the JSON content
            rule_content = json.loads(json_content)

            # Add rule_selection section if it doesn't exist
            if "rule_selection" not in rule_content:
                rule_content["rule_selection"] = {
                    "description": "Select the appropriate rule based on your current task:",
                    "contexts": {},
                }
            elif "contexts" not in rule_content["rule_selection"]:
                rule_content["rule_selection"]["contexts"] = {}

            # Add line_count_metadata section if it doesn't exist
            if "line_count_metadata" not in rule_content:
                rule_content["line_count_metadata"] = {"rules": []}

            # Add fetch_read_mapping section if it doesn't exist
            if "fetch_read_mapping" not in rule_content:
                rule_content["fetch_read_mapping"] = {
                    "table": "| Rule Reference | Access Method |\n|----|----|\n"
                }

            # Clear existing sections to rebuild them
            rule_content["line_count_metadata"]["rules"] = []

            # Create a fresh table header for fetch_read_mapping
            rule_content["fetch_read_mapping"][
                "table"
            ] = "| Rule Reference | Access Method |\n|----|----|\n"

            # Add parent rule to fetch_read_mapping
            parent_id = parent_path.stem.split("-")[0]
            parent_mapping_entry = f'| {parent_id} | `fetch_rules(["{parent_id}"])` |'
            rule_content["fetch_read_mapping"]["table"] += parent_mapping_entry + "\n"

            # Create parent subdirectory structure
            parent_dir = parent_path.parent / parent_path.stem
            logger.info(f"Creating parent directory: {parent_dir}")
            parent_dir.mkdir(parents=True, exist_ok=True)
            # Additional debug info
            logger.info(f"Directory exists after creation: {parent_dir.exists()}")
            logger.info(f"Directory is writable: {os.access(parent_dir, os.W_OK)}")
            if parent_dir.exists():
                logger.info(f"Directory contents: {list(parent_dir.iterdir())}")

            # Add each child rule reference
            contexts = {}
            for child in child_rules:
                child_id = child.get("id")
                child_name = child.get("name")
                child_path = child.get("relative_path")
                child_line_count = child.get(
                    "line_count", 100
                )  # Default to 100 if not provided

                if not child_id or not child_name or not child_path:
                    logger.warning(
                        f"Incomplete child rule data: id={child_id}, name={child_name}, path={child_path}"
                    )
                    continue

                # Add to line_count_metadata
                rule_content["line_count_metadata"]["rules"].append(
                    f"`{child_id}-{child_name}.mdc` - {child_line_count} lines"
                )

                # Add to fetch_read_mapping table
                read_file_cmd = f'read_file("{child_path}", should_read_entire_file=false, start_line_one_indexed=1, end_line_one_indexed_inclusive={child_line_count})'
                mapping_entry = f"| {child_id} | `{read_file_cmd}` |"
                rule_content["fetch_read_mapping"]["table"] += mapping_entry + "\n"

                # Format for rule_selection section
                child_key = f"{child_name.replace('-', '_')}"

                # Use the description from the child rule or create a default one
                child_description = child.get(
                    "description",
                    f"WHEN working with {child_name.replace('-', ' ')} TO ensure quality you MUST follow THESE {child_name.replace('-', ' ')} guidelines",
                )

                # Create the context entry for rule_selection
                contexts[child_key] = {
                    "description": child_description,
                    "command": f'read_file("{child_path}", should_read_entire_file=false, start_line_one_indexed=1, end_line_one_indexed_inclusive={child_line_count})',
                }

                # Move the child file to the parent directory
                try:
                    # Get the child file path
                    child_file_path = Path(self.output_dir.parent / child_path)
                    if child_file_path.exists():
                        # Construct the destination path
                        parts = child_id.split(".")
                        if len(parts) > 1:
                            # Format as parent-xx-name.mdc
                            formatted_id = "-".join(parts)
                        else:
                            formatted_id = child_id

                        dest_filename = f"{formatted_id}-{child_name}.mdc"
                        dest_path = parent_dir / dest_filename

                        # Copy the file
                        logger.info(f"Moving child rule {child_id} to {dest_path}")

                        # Ensure parent directory exists
                        dest_path.parent.mkdir(parents=True, exist_ok=True)

                        # Read content from original file
                        with open(child_file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Write to new location
                        with open(dest_path, "w", encoding="utf-8") as f:
                            f.write(content)

                        # Only remove original file if copy was successful
                        if dest_path.exists():
                            try:
                                child_file_path.unlink()
                                logger.info(
                                    f"Successfully moved child rule {child_id} to {dest_path}"
                                )
                            except Exception as e:
                                logger.error(f"Error removing original file: {e}")
                        else:
                            logger.error(f"Failed to create {dest_path}")
                    else:
                        logger.warning(f"Child rule file not found: {child_file_path}")
                except Exception as e:
                    logger.error(f"Error moving child rule {child_id}: {e}")

            # Replace the rule_selection section with the new contexts
            rule_content["rule_selection"]["contexts"] = contexts

            # Write the updated content back to the file
            with open(parent_path, "w", encoding="utf-8") as f:
                f.write("---")
                f.write(frontmatter)
                f.write("---\n")
                f.write(json.dumps(rule_content, indent=2))

            logger.info(
                f"Updated parent rule with references to {len(child_rules)} child rules"
            )
            return True

        except Exception as e:
            logger.error(f"Error updating parent rule {parent_path}: {str(e)}")
            return False

    def update_all_parent_child_relationships(
        self, path_map: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Update all parent-child relationships based on a path map.

        Args:
            path_map: Mapping of rule IDs to path information
        """
        # First, identify all direct parent-child relationships
        for rule_id, rule_info in path_map.items():
            # Skip if not a parent rule
            if rule_info["level"] != 0:
                continue

            # Get children for this parent
            children = list(rule_info["children"].values())

            # If this rule has children, update its references
            if children:
                child_data = []
                for child in children:
                    # Calculate line count for the child rule
                    line_count = 100  # Default
                    try:
                        if child["full_path"].exists():
                            with open(child["full_path"], "r", encoding="utf-8") as f:
                                content = f.read()
                                line_count = len(content.splitlines())
                    except Exception as e:
                        logger.warning(
                            f"Error calculating line count for {child['id']}: {str(e)}"
                        )

                    # Add child data
                    child_data.append(
                        {
                            "id": child["id"],
                            "name": child["name"],
                            "relative_path": child["relative_path"],
                            "line_count": line_count,
                            "description": child.get("description", ""),
                        }
                    )

                # Update the parent rule with references to its children
                self.update_parent_with_children(rule_info["full_path"], child_data)

        # Then, handle grandparent-grandchild relationships
        for rule_id, rule_info in path_map.items():
            # Only process child rules that might have grandchildren
            if rule_info["level"] != 1:
                continue

            # Get grandchildren for this parent
            grandchildren = list(rule_info["children"].values())

            # If this rule has grandchildren, update its references
            if grandchildren:
                grandchild_data = []
                for grandchild in grandchildren:
                    # Calculate line count for the grandchild rule
                    line_count = 100  # Default
                    try:
                        if grandchild["full_path"].exists():
                            with open(
                                grandchild["full_path"], "r", encoding="utf-8"
                            ) as f:
                                content = f.read()
                                line_count = len(content.splitlines())
                    except Exception as e:
                        logger.warning(
                            f"Error calculating line count for {grandchild['id']}: {str(e)}"
                        )

                    # Add grandchild data
                    grandchild_data.append(
                        {
                            "id": grandchild["id"],
                            "name": grandchild["name"],
                            "relative_path": grandchild["relative_path"],
                            "line_count": line_count,
                            "description": grandchild.get("description", ""),
                        }
                    )

                # Update the child rule with references to its grandchildren
                self.update_parent_with_children(
                    rule_info["full_path"], grandchild_data
                )
