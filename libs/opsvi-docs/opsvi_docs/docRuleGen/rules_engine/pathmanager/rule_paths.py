# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Rule Path Manager Module","description":"This module provides functions for managing paths and directory structures for documentation rules, ensuring rules are created in the correct location.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Import necessary modules for functionality.","line_start":3,"line_end":12},{"name":"Logging Configuration","description":"Configure logging settings for the module.","line_start":13,"line_end":14},{"name":"RulePathManager Class","description":"Class that manages rule paths and directory structure for documentation rules.","line_start":15,"line_end":271}],"key_elements":[{"name":"RulePathManager","description":"Class that manages rule paths and directory structure for documentation rules.","line":17},{"name":"__init__","description":"Constructor for initializing the RulePathManager with an output directory.","line":23},{"name":"determine_rule_path","description":"Determines the proper path for a rule based on its ID and parent.","line":36},{"name":"get_full_rule_path","description":"Gets the full path for a rule file.","line":132},{"name":"get_relative_path","description":"Gets the path relative to the output directory's parent.","line":147},{"name":"get_reference_path","description":"Gets the relative path for a rule file, suitable for use in references.","line":163},{"name":"process_taxonomy_paths","description":"Processes a taxonomy and determines all rule paths up front.","line":178}]}
"""
# FILE_MAP_END

"""
Rule Path Manager Module for Documentation Rule Generator.

This module provides functions for managing paths and directory structures
for documentation rules, ensuring rules are created in the correct location.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RulePathManager:
    """
    Manages rule paths and directory structure for documentation rules.
    Ensures rules are created in their proper locations based on hierarchy.
    """

    def __init__(self, output_dir: str = ".cursor/rules"):
        """
        Initialize the path manager.

        Args:
            output_dir: Base directory for rules output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Cache of computed paths to avoid recalculation
        self._path_cache = {}

    def determine_rule_path(
        self, rule_id: str, rule_name: str, parent_id: Optional[str] = None
    ) -> Tuple[Path, str]:
        """
        Determine the proper path for a rule based on its ID and parent.
        Creates the necessary directories if they don't exist.

        Args:
            rule_id: ID of the rule (e.g., '301', '301.01', '301.01.1')
            rule_name: Name of the rule
            parent_id: ID of the parent rule (if any)

        Returns:
            Tuple of (directory_path, file_name)
        """
        cache_key = f"{rule_id}:{rule_name}:{parent_id}"
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]

        # Default - place in root output directory
        directory_path = self.output_dir
        file_name = f"{rule_id}-{rule_name}.mdc"

        # Check if this is a child or grandchild rule by counting the dots
        hierarchy_level = rule_id.count(".") if "." in rule_id else 0

        if hierarchy_level == 0:
            # This is a parent rule - place in root output directory
            pass
        elif hierarchy_level == 1:
            # This is a child rule - place in parent's directory
            # Extract parent ID (part before the dot)
            parent_rule_id = rule_id.split(".")[0]

            # Find the parent rule's directory
            parent_rule_files = list(self.output_dir.glob(f"{parent_rule_id}-*.mdc"))
            if parent_rule_files:
                parent_file = parent_rule_files[0]
                parent_dir_name = parent_file.stem  # Get filename without extension

                # Create parent directory if it doesn't exist
                directory_path = self.output_dir / parent_dir_name
                directory_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Using parent directory: {directory_path}")
            else:
                logger.warning(
                    f"Parent rule file for {rule_id} not found, using root directory"
                )

            # Create a properly formatted file name (e.g., 301-01-documentation-principles.mdc)
            parts = rule_id.split(".")
            formatted_id = f"{parts[0]}-{parts[1]}"
            file_name = f"{formatted_id}-{rule_name}.mdc"

        elif hierarchy_level == 2:
            # This is a grandchild rule - handle the nested directory structure
            parts = rule_id.split(".")
            parent_rule_id = parts[0]
            immediate_parent_id = f"{parts[0]}.{parts[1]}"

            # First, get the parent's directory
            parent_rule_files = list(self.output_dir.glob(f"{parent_rule_id}-*.mdc"))
            if parent_rule_files:
                # Create the parent directory path
                parent_file = parent_rule_files[0]
                parent_dir_name = parent_file.stem
                parent_dir = self.output_dir / parent_dir_name

                # Check if immediate parent has a directory
                immediate_parent_formatted = immediate_parent_id.replace(".", "-")
                immediate_parent_paths = list(
                    parent_dir.glob(f"{immediate_parent_formatted}-*.mdc")
                )

                if immediate_parent_paths:
                    immediate_parent_file = immediate_parent_paths[0]
                    immediate_parent_dir_name = immediate_parent_file.stem

                    # Create the grandchild directory
                    directory_path = parent_dir / immediate_parent_dir_name
                    directory_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Using grandchild directory: {directory_path}")
                else:
                    # If immediate parent's directory doesn't exist, use the parent directory
                    directory_path = parent_dir
                    logger.warning(
                        f"Immediate parent directory for {rule_id} not found, using parent directory"
                    )
            else:
                logger.warning(
                    f"Parent rule file for {rule_id} not found, using root directory"
                )

            # Create a properly formatted file name for grandchild (e.g., 301-02-1-directory-organization.mdc)
            formatted_id = f"{parts[0]}-{parts[1]}-{parts[2]}"
            file_name = f"{formatted_id}-{rule_name}.mdc"

        # Create the directory if it doesn't exist
        directory_path.mkdir(parents=True, exist_ok=True)

        # Cache the result
        result = (directory_path, file_name)
        self._path_cache[cache_key] = result

        return result

    def get_full_rule_path(
        self, rule_id: str, rule_name: str, parent_id: Optional[str] = None
    ) -> Path:
        """
        Get the full path for a rule file.

        Args:
            rule_id: ID of the rule
            rule_name: Name of the rule
            parent_id: ID of the parent rule (if any)

        Returns:
            Path to the rule file
        """
        directory, filename = self.determine_rule_path(rule_id, rule_name, parent_id)
        return directory / filename

    def get_relative_path(self, full_path: Path) -> str:
        """
        Get the path relative to the output directory's parent.

        Args:
            full_path: Full path to a rule file

        Returns:
            Relative path as a string
        """
        try:
            return str(full_path.relative_to(self.output_dir.parent))
        except ValueError:
            # If relative_to raises an error, return the full path
            return str(full_path)

    def get_reference_path(
        self, rule_id: str, rule_name: str, parent_id: Optional[str] = None
    ) -> str:
        """
        Get the relative path for a rule file, suitable for use in references.

        Args:
            rule_id: ID of the rule
            rule_name: Name of the rule
            parent_id: ID of the parent rule (if any)

        Returns:
            Relative path as a string
        """
        full_path = self.get_full_rule_path(rule_id, rule_name, parent_id)
        return self.get_relative_path(full_path)

    def process_taxonomy_paths(
        self, taxonomy: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Process a taxonomy and determine all rule paths up front.

        Args:
            taxonomy: The taxonomy dictionary

        Returns:
            Dictionary mapping rule IDs to path information
        """
        path_map = {}

        # Process each category
        for category in taxonomy.get("categories", []):
            # Process parent rules
            for parent_rule in category.get("rules", []):
                parent_id = parent_rule.get("id")
                parent_name = parent_rule.get("name")

                if parent_id and parent_name:
                    # Determine parent rule path
                    directory, filename = self.determine_rule_path(
                        parent_id, parent_name
                    )
                    full_path = directory / filename

                    path_map[parent_id] = {
                        "id": parent_id,
                        "name": parent_name,
                        "directory": directory,
                        "filename": filename,
                        "full_path": full_path,
                        "relative_path": self.get_relative_path(full_path),
                        "parent_id": None,
                        "level": 0,
                        "children": {},
                    }

                    # Process child rules
                    for child_rule in parent_rule.get("child_rules", []):
                        child_id = child_rule.get("id")
                        child_name = child_rule.get("name")

                        if child_id and child_name:
                            # Determine child rule path
                            child_directory, child_filename = self.determine_rule_path(
                                child_id, child_name, parent_id
                            )
                            child_full_path = child_directory / child_filename

                            # Add to path map
                            path_map[child_id] = {
                                "id": child_id,
                                "name": child_name,
                                "directory": child_directory,
                                "filename": child_filename,
                                "full_path": child_full_path,
                                "relative_path": self.get_relative_path(
                                    child_full_path
                                ),
                                "parent_id": parent_id,
                                "level": 1,
                                "children": {},
                            }

                            # Add to parent's children
                            if parent_id in path_map:
                                path_map[parent_id]["children"][child_id] = path_map[
                                    child_id
                                ]

                            # Process grandchild rules
                            for grandchild_rule in child_rule.get("child_rules", []):
                                grandchild_id = grandchild_rule.get("id")
                                grandchild_name = grandchild_rule.get("name")

                                if grandchild_id and grandchild_name:
                                    # Determine grandchild rule path
                                    (
                                        gc_directory,
                                        gc_filename,
                                    ) = self.determine_rule_path(
                                        grandchild_id, grandchild_name, child_id
                                    )
                                    gc_full_path = gc_directory / gc_filename

                                    # Add to path map
                                    path_map[grandchild_id] = {
                                        "id": grandchild_id,
                                        "name": grandchild_name,
                                        "directory": gc_directory,
                                        "filename": gc_filename,
                                        "full_path": gc_full_path,
                                        "relative_path": self.get_relative_path(
                                            gc_full_path
                                        ),
                                        "parent_id": child_id,
                                        "level": 2,
                                        "children": {},
                                    }

                                    # Add to parent's children
                                    if child_id in path_map:
                                        path_map[child_id]["children"][
                                            grandchild_id
                                        ] = path_map[grandchild_id]

        return path_map
