# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Code File Processor","description":"This module provides specialized processing for code files like Python, JavaScript, etc., including structure analysis and file map generation.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation string explaining the purpose of the module.","line_start":3,"line_end":6},{"name":"Imports","description":"Import statements for required modules and classes.","line_start":7,"line_end":16},{"name":"CodeFileProcessor Class","description":"Class for processing code files, inheriting from FileProcessor.","line_start":18,"line_end":204}],"key_elements":[{"name":"CodeFileProcessor","description":"Class for processing code files.","line":18},{"name":"analyze_structure","description":"Asynchronous method to analyze the structure of code files.","line":20},{"name":"generate_file_map","description":"Asynchronous method to generate a file map for code files.","line":66},{"name":"extract_existing_file_map","description":"Function imported from file_utils to extract existing file maps.","line":16},{"name":"calculate_file_hash","description":"Function imported from file_utils to calculate the hash of file content.","line":16}]}
"""
# FILE_MAP_END

"""
Code file processor for genfilemap.

This module provides specialized processing for code files like Python, JavaScript, etc.
"""

import re
import json
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

from genfilemap.processors.base import FileProcessor
from genfilemap.prompting.prompts import get_code_system_message, get_code_user_prompt
from genfilemap.utils.file_utils import extract_existing_file_map, calculate_file_hash


class CodeFileProcessor(FileProcessor):
    """Processor for code files"""

    async def analyze_structure(self, content: str) -> Dict[str, Any]:
        """
        Analyze the code structure to provide hints for the LLM.

        Returns information about functions, classes, imports, and other code constructs.
        """
        # Start with basic analysis from parent class
        analysis = await super().analyze_structure(content)

        # Extract functions, classes, and imports
        functions = []
        classes = []
        imports = []

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Simple function detection (can be improved)
            if re.match(r"^\s*def\s+\w+\s*\(", line):
                functions.append(
                    {
                        "name": re.search(r"def\s+(\w+)", line).group(1),
                        "line": i + 1,  # 1-indexed line numbers
                    }
                )

            # Simple class detection (can be improved)
            if re.match(r"^\s*class\s+\w+", line):
                classes.append(
                    {
                        "name": re.search(r"class\s+(\w+)", line).group(1),
                        "line": i + 1,  # 1-indexed line numbers
                    }
                )

            # Simple import detection (can be improved)
            if re.match(r"^\s*(import|from)\s+", line):
                imports.append(
                    {"statement": line.strip(), "line": i + 1}  # 1-indexed line numbers
                )

        # Add code-specific analysis
        analysis["functions"] = functions
        analysis["classes"] = classes
        analysis["imports"] = imports

        return analysis

    async def generate_file_map(
        self, content: str, comment_style: Tuple[str, str, str]
    ) -> Optional[str]:
        """
        Generate a file map specialized for code files.

        Uses code structure analysis to guide the LLM in creating an accurate file map.
        """
        start_multi, end_multi, single_line = comment_style

        # Extract existing file map if it exists
        existing_map, remaining_content = extract_existing_file_map(
            content, comment_style
        )

        # Calculate hash of the content without the file map
        content_hash = calculate_file_hash(remaining_content)

        # Check if there's a stored hash for this file
        hash_file = f"{self.file_path}.hash"
        if os.path.exists(hash_file):
            with open(hash_file, "r") as f:
                stored_hash = f.read().strip()

            print(f"DEBUG: Stored hash: {stored_hash}")
            print(f"DEBUG: Current hash: {content_hash}")

            # If hash matches and we have an existing map, check if it's valid
            if stored_hash == content_hash and existing_map:
                # First try to match Python triple-quoted format
                pattern = r'"""\s*FILE_MAP_BEGIN\s*"""(?:\s*)(.*?)(?:\s*)"""\s*"""\s*FILE_MAP_END\s*"""'
                json_match = re.search(pattern, existing_map, re.DOTALL)

                # If not found, try other formats
                if not json_match:
                    pattern = r"(?:\/\*|\<!--)\s*(\{.*?\})\s*(?:\*\/|\-->)"
                    json_match = re.search(pattern, existing_map, re.DOTALL)

                if json_match:
                    file_map_json = json_match.group(1).strip()
                    if await self.validate_generated_map(file_map_json, content):
                        print(
                            "DEBUG: Hash matches and existing map is valid, no need to update"
                        )
                        return None  # Valid file map, no need to update
                    else:
                        print("DEBUG: Hash matches but existing map failed validation")
                else:
                    print(
                        "DEBUG: Hash matches but couldn't extract JSON from existing map"
                    )
            elif stored_hash == content_hash:
                print("DEBUG: Hash matches but no existing map found")
            else:
                print("DEBUG: Hash does not match, generating new file map")
        else:
            print(f"DEBUG: No hash file found, will generate new map")

        # Get the current date
        current_date = datetime.now().strftime("%Y-%m-%d")

        # IMPORTANT CHANGE: Add padding lines to the beginning of the content
        # This naturally accounts for the file map that will be inserted
        # For HTML-style comments (used in Markdown), we need to add more padding lines
        # because the file map now takes 5 lines + 1 blank line = 6 lines total
        if start_multi == "<!--":
            # Add 6 blank lines for HTML comments (5 for file map + 1 blank line)
            content_with_blanks = "\n\n\n\n\n\n" + remaining_content
            print(
                f"DEBUG-CODE: Added six blank lines to beginning of content for HTML comment format"
            )
        else:
            # Add 2 blank lines for other file types (1 for file map + 1 blank line)
            content_with_blanks = "\n\n" + remaining_content
            print(
                f"DEBUG-CODE: Added two blank lines to beginning of content for standard format"
            )

        # Perform structure analysis
        structure_analysis = await self.analyze_structure(remaining_content)
        print(f"DEBUG-CODE: Structure analysis completed")

        # Get messages for LLM
        system_message = get_code_system_message()
        user_prompt = get_code_user_prompt(
            file_path=self.file_path,
            file_type=self.file_type,
            current_date=current_date,
            content=content_with_blanks,  # Use the content with blank lines
            structure_analysis=structure_analysis,
        )

        # Generate with exponential backoff for rate limits
        max_retries = 5
        base_delay = 1
        file_map_json = None

        for attempt in range(max_retries):
            try:
                result = await self.api_client.generate_completion(
                    system_message, user_prompt, self.model
                )

                # Try to parse as JSON
                try:
                    file_map_obj = json.loads(result)

                    # No need for check_and_fix_line_numbers anymore since the line numbers
                    # will already be correct due to the blank lines added to the content

                    # Validate against our schema
                    valid = await self.validate_generated_map(
                        json.dumps(file_map_obj), content
                    )

                    if valid:
                        # Single-line JSON formatting - most compact representation
                        file_map_json = json.dumps(file_map_obj, separators=(",", ":"))
                        break
                    else:
                        print(
                            f"Generated file map failed validation for {self.file_path} (attempt {attempt+1})"
                        )
                except (json.JSONDecodeError, ValueError) as e:
                    print(
                        f"Invalid JSON response from LLM (attempt {attempt+1}): {str(e)}"
                    )
                    if attempt == max_retries - 1:
                        raise ValueError(
                            f"Failed to generate valid file map JSON after {max_retries} attempts"
                        )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = base_delay * (2**attempt)
                print(f"API error. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)

        # If we couldn't generate a valid file map, return None
        if not file_map_json:
            return None

        # Format the file map with the appropriate comment style
        if start_multi and end_multi:
            # Special format for Python files to avoid syntax errors with adjacent triple quotes
            if start_multi == '"""':
                formatted_map = (
                    f'# FILE_MAP_BEGIN\n"""\n{file_map_json}\n"""\n# FILE_MAP_END\n\n'
                )
                print("DEBUG: Using Python-compatible file map format with # markers")
            else:
                # Use multi-line comment style for other file types
                formatted_map = f"{start_multi} FILE_MAP_BEGIN {start_multi} {file_map_json} {end_multi} {end_multi} FILE_MAP_END {end_multi}\n\n"
        elif single_line:
            # Fall back to single-line comments if needed
            formatted_map = f"{single_line}FILE_MAP_BEGIN {single_line} {file_map_json} {single_line} FILE_MAP_END\n\n"
        else:
            # Use generic comment style as a last resort
            formatted_map = (
                f"/* FILE_MAP_BEGIN */ /* {file_map_json} */ /* FILE_MAP_END */\n\n"
            )

        # Save the current hash
        with open(hash_file, "w") as f:
            f.write(content_hash)

        return formatted_map
