
"""
Project map generation for GenFileMap.

This module provides functionality for generating project-level file maps.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import fnmatch
import datetime

from genfilemap.logging_utils import info, debug, error
from genfilemap.config import get_config_value
from genfilemap.utils.file_utils import should_ignore_file, load_ignore_patterns
from genfilemap.core.file_operations import count_lines

def generate_project_map(config: Dict[str, Any]) -> bool:
    """
    Generate a project-level file map that consolidates references to all project files and their file maps.

    Args:
        config: Configuration dictionary

    Returns:
        bool: True if successful, False otherwise
    """
    # Only generate if explicitly requested
    if not get_config_value(config, "project_map", False):
        return True

    path = get_config_value(config, "path")
    recursive = get_config_value(config, "file_processing.recursive")
    include = get_config_value(config, "file_processing.include_extensions")
    exclude = get_config_value(config, "file_processing.exclude_extensions")
    min_lines = get_config_value(config, "file_processing.min_lines", 0)

    # Get output directory configuration
    maps_dir = get_config_value(config, "output_dirs.maps", "map_reports")

    # Get output file configuration
    output_filename = get_config_value(config, "project_map.output_file", "project_map.json")

    # Get JSON formatting options
    compact_json = get_config_value(config, "project_map.compact_json", False)
    compact_level = get_config_value(config, "project_map.compact_level", 2 if compact_json else 0)

    # Ensure we have an absolute path to the map_reports directory
    if not os.path.isabs(maps_dir):
        maps_dir = os.path.abspath(maps_dir)

    # Create the directory if it doesn't exist
    os.makedirs(maps_dir, exist_ok=True)

    # Use a fixed output path in the map_reports directory
    output_file = os.path.join(maps_dir, output_filename)

    debug(f"Project map will be written to: {output_file}")

    ignore_pathspec = config.get('ignore_pathspec')

    debug(f"Generating project map for {path} (recursive={recursive})")
    debug(f"Using ignore_pathspec: {ignore_pathspec}")
    debug(f"Output file will be: {output_file}")

    # Initialize project map structure with current timestamp
    timestamp = datetime.datetime.now().isoformat()

    project_map = {
        "project_name": os.path.basename(os.path.abspath(path)),
        "base_path": os.path.abspath(path),
        "files": [],
        "generated_at": timestamp
    }

    # Collect file data
    files_found = 0
    files_with_maps = 0

    try:
        # Function to extract file map from content
        def extract_file_map(content: str) -> Optional[Dict[str, Any]]:
            # Look for JSON in common file map patterns
            patterns = [
                r'(?:# |\/\*|<!--) FILE_MAP_BEGIN.*?(?:`|"""|\*\/|-->)\s*\n(?:`|"""|\/\*|<!--)\s*\n(.*?)\n\s*(?:`|"""|\/\*|-->)\s*\n(?:# |\/\*|<!--) FILE_MAP_END',
                r'(?:# |\/\*|<!--) FILE_MAP_BEGIN (?:# |\/\*|<!--) (.*?) (?:`|"""|\/\*|-->) (?:# |\/\*|<!--) FILE_MAP_END (?:`|"""|\/\*|-->)',
                r'(?:# |\/\*|<!--)FILE_MAP_BEGIN (?:# |\/\*|<!--) (.*?) (?:# |\/\*|<!--) FILE_MAP_END'
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        continue

            # Add more specific patterns for common formats
            # Python single-line comment format (new)
            python_single_line_pattern = r'# FILE_MAP_BEGIN\s*\n((?:# .*\n)+)# FILE_MAP_END'
            match = re.search(python_single_line_pattern, content, re.DOTALL)
            if match:
                try:
                    captured_content = match.group(1)
                    json_lines = [line[2:] for line in captured_content.split('\n') if line.startswith('# ')]
                    json_content = '\n'.join(json_lines)
                    return json.loads(json_content)
                except:
                    debug("Failed to parse Python single-line comment format file map JSON")

            # Python format with triple quotes (old)
            python_pattern = r'# FILE_MAP_BEGIN\s*\n"""\s*\n(.*?)\n\s*"""\s*\n# FILE_MAP_END'
            match = re.search(python_pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    debug("Failed to parse Python format file map JSON")

            # HTML/Markdown format
            html_pattern = r'<!-- FILE_MAP_BEGIN\s*\n<!--\s*\n(.*?)\n\s*-->\s*\n<!-- FILE_MAP_END -->'
            match = re.search(html_pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    debug("Failed to parse HTML format file map JSON")

            return None

        # Traverse directory and collect file maps
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path) if recursive else [(path, None, os.listdir(path))]:
                if dirs is not None:
                    dirs[:] = [d for d in dirs if not should_ignore_file(os.path.join(root, d), pathspec_obj=ignore_pathspec)]
                for filename in files:
                    file_path = os.path.join(root, filename)
                    if not os.path.isfile(file_path):
                        continue
                    if should_ignore_file(file_path, pathspec_obj=ignore_pathspec):
                        continue

                    # Get relative path for pattern matching
                    rel_path = os.path.relpath(file_path, path)

                    # Check extensions
                    ext = os.path.splitext(file_path)[1].lower()
                    if include and ext not in include:
                        debug(f"Skipping {rel_path}: extension not in include list")
                        continue
                    if exclude and ext in exclude:
                        debug(f"Skipping {rel_path}: extension in exclude list")
                        continue

                    # Check minimum line count
                    if min_lines > 0:
                        line_count = count_lines(file_path)
                        if line_count < min_lines:
                            debug(f"Skipping {rel_path}: only {line_count} lines (minimum: {min_lines})")
                            continue

                    files_found += 1

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(10000)  # Read only first part to find file map

                            # Check for file map markers
                            has_file_map = False
                            file_metadata = None

                            # Check for file map markers
                            if "FILE_MAP_BEGIN" in content and "FILE_MAP_END" in content:
                                debug(f"Found FILE_MAP markers in {rel_path}")
                                file_map = extract_file_map(content)
                                if file_map:
                                    debug(f"Successfully extracted file map from {rel_path}")
                                    if isinstance(file_map, dict) and "file_metadata" in file_map:
                                        has_file_map = True
                                        files_with_maps += 1
                                        file_metadata = file_map["file_metadata"]
                                        debug(f"Found valid file map with metadata in {rel_path}")
                                    else:
                                        debug(f"File map in {rel_path} is missing metadata: {file_map}")
                                else:
                                    debug(f"Failed to extract file map from {rel_path} despite finding markers")

                            # Add file to project map
                            if file_metadata:
                                debug(f"Adding {rel_path} with has_file_map=True")
                                project_map["files"].append({
                                    "path": rel_path,
                                    "type": file_metadata.get("type", "unknown"),
                                    "title": file_metadata.get("title", os.path.basename(file_path)),
                                    "description": file_metadata.get("description", ""),
                                    "has_file_map": True
                                })
                            else:
                                # Determine file type based on extension
                                file_type = "unknown"
                                if ext in [".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rs"]:
                                    file_type = "code"
                                elif ext in [".md", ".txt", ".rst"]:
                                    file_type = "documentation"
                                elif ext in [".html", ".css"]:
                                    file_type = "markup"
                                elif ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"]:
                                    file_type = "configuration"

                                project_map["files"].append({
                                    "path": rel_path,
                                    "type": file_type,
                                    "title": os.path.basename(file_path),
                                    "has_file_map": False
                                })
                    except Exception as e:
                        error(f"Error processing {file_path} for project map: {str(e)}")

                # Exit after first level if not recursive
                if not recursive:
                    break

        # Write project map to file
        # Ensure the directory exists - but only create directories, not files
        output_dir = os.path.dirname(os.path.abspath(output_file))
        if output_dir and output_dir != '':  # Only create directories if there's a valid directory path
            os.makedirs(output_dir, exist_ok=True)

        # Handle file existence explicitly - remove the file if it exists
        if os.path.exists(output_file):
            try:
                # Check if the output_file is actually a directory
                if os.path.isdir(output_file):
                    debug(f"Output path '{output_file}' is a directory, not a file. Using file inside this directory.")
                    # Use the original output_filename inside this directory
                    output_file = os.path.join(output_file, output_filename)
                    debug(f"Adjusted output file path to: {output_file}")
                else:
                    # It's a file, so we can safely remove it
                    debug(f"Removing existing project map file: {output_file}")
                    os.remove(output_file)
            except Exception as e:
                error(f"Failed to handle existing project map path: {str(e)}")
                return False

        # Process the file list for a more efficient representation
        if compact_level >= 2:
            # Group files by type to make the output more manageable
            files_by_type = {}
            for file_entry in project_map["files"]:
                file_type = file_entry.get("type", "unknown")
                if file_type not in files_by_type:
                    files_by_type[file_type] = []
                files_by_type[file_type].append(file_entry)

            # Replace the flat file list with the grouped structure
            if compact_level >= 3:
                # Level 3: Super compact - just paths organized by type
                compact_files = {}
                for file_type, files in files_by_type.items():
                    compact_files[file_type] = [f["path"] for f in files]
                project_map["files_by_type"] = compact_files
                del project_map["files"]
            else:
                # Level 2: More detailed but still compact
                project_map["files_by_type"] = files_by_type
                del project_map["files"]

        # Write to the file with appropriate JSON formatting
        with open(output_file, 'w', encoding='utf-8') as f:
            if compact_level == 1:
                # Level 1: No indentation, but keep some spacing
                json.dump(project_map, f, separators=(', ', ': '))
            elif compact_level >= 2:
                # Level 2+: Fully minified JSON
                json.dump(project_map, f, separators=(',', ':'))
            else:
                # Level 0: Normal indented format
                json.dump(project_map, f, indent=2)

        info(f"Project map generated at {os.path.abspath(output_file)}")
        info(f"Found {files_found} files, {files_with_maps} with file maps")
        return True

    except Exception as e:
        error(f"Error generating project map: {str(e)}")
        return False