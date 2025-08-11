# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Documentation File Processor","description":"This module provides specialized processing for documentation files like markdown, including structure analysis and file map generation.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation for the module's purpose and functionality.","line_start":2,"line_end":5},{"name":"Imports","description":"Import statements for necessary libraries and modules.","line_start":6,"line_end":17},{"name":"DocumentationFileProcessor Class","description":"Class for processing documentation files, inheriting from FileProcessor.","line_start":18,"line_end":36},{"name":"analyze_structure Method","description":"Asynchronously analyzes the document structure to provide hints for the LLM.","line_start":37,"line_end":66},{"name":"generate_file_map Method","description":"Asynchronously generates a file map specialized for documentation files.","line_start":67,"line_end":186}],"key_elements":[{"name":"DocumentationFileProcessor","description":"Class for processing documentation files.","line":19},{"name":"analyze_structure","description":"Method to analyze the structure of the document.","line":38},{"name":"generate_file_map","description":"Method to generate a file map for documentation files.","line":67},{"name":"headings","description":"List to store extracted headings from the document.","line":45},{"name":"content_hash","description":"Hash of the content without the file map.","line":113},{"name":"hash_file","description":"Path to the hash file for the current document.","line":115},{"name":"current_date","description":"Current date formatted as a string.","line":152},{"name":"file_map_json","description":"JSON representation of the generated file map.","line":183}]}
"""
# FILE_MAP_END

"""
Documentation file processor for genfilemap.

This module provides specialized processing for documentation files like markdown.
"""

import re
import json
import asyncio
import hashlib
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

from genfilemap.processors.base import FileProcessor
from genfilemap.prompting.prompts import (
    get_documentation_system_message,
    get_documentation_user_prompt,
)
from genfilemap.utils.file_utils import extract_existing_file_map, calculate_file_hash


class DocumentationFileProcessor(FileProcessor):
    """Processor for documentation files"""

    async def analyze_structure(self, content: str) -> Dict[str, Any]:
        """
        Analyze the document structure to provide hints for the LLM.

        Returns information about headings, sections, and overall structure.
        """
        # Start with basic analysis from parent class
        analysis = await super().analyze_structure(content)

        # Extract headings from markdown
        headings = []
        heading_pattern = r"^(#{1,6})\s+(.+?)(?:\s*#{1,6})?$"

        lines = content.split("\n")
        for i, line in enumerate(lines):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append(
                    {
                        "level": level,
                        "text": text,
                        "line": i + 1,  # 1-indexed line numbers
                    }
                )

        # Add heading information to the analysis
        analysis["headings"] = headings

        return analysis

    async def generate_file_map(
        self, content: str, comment_style: Tuple[str, str, str]
    ) -> Optional[str]:
        """
        Generate a file map specialized for documentation files.

        Uses document structure analysis to guide the LLM in creating an accurate file map.
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

            # If hash matches and we have an existing map, check if it's valid
            if stored_hash == content_hash and existing_map:
                # Try to extract JSON from existing map
                pattern = r"(?:\/\*|\<!--)\s*(\{.*?\})\s*(?:\*\/|\-->)"
                json_match = re.search(pattern, existing_map, re.DOTALL)
                if json_match:
                    file_map_json = json_match.group(1).strip()
                    try:
                        file_map_obj = json.loads(file_map_json)
                        valid = await self.validate_generated_map(
                            file_map_json, content
                        )
                        if valid:
                            print(
                                f"DEBUG-DOC: Existing map is valid, returning None to skip update"
                            )
                            return None  # Valid file map, no need to update
                    except json.JSONDecodeError:
                        print(f"DEBUG-DOC: Invalid JSON in existing map")
                else:
                    print(f"DEBUG-DOC: No JSON found in existing map")
        else:
            print(f"DEBUG-DOC: No hash file found, will generate new map")

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
                f"DEBUG-DOC: Added six blank lines to beginning of content for HTML comment format"
            )
        else:
            # Add 2 blank lines for other file types (1 for file map + 1 blank line)
            content_with_blanks = "\n\n" + remaining_content
            print(
                f"DEBUG-DOC: Added two blank lines to beginning of content for standard format"
            )

        # Perform structure analysis on the original content
        structure_analysis = await self.analyze_structure(remaining_content)
        print(
            f"DEBUG-DOC: Structure analysis completed with {len(structure_analysis.get('headings', []))} headings"
        )

        # Get messages for LLM
        system_message = get_documentation_system_message()
        user_prompt = get_documentation_user_prompt(
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

        print(f"DEBUG-DOC: Starting LLM generation with {max_retries} max retries")
        for attempt in range(max_retries):
            try:
                print(f"DEBUG-DOC: LLM generation attempt {attempt+1}")
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
                    print(f"DEBUG-DOC: Map validation result: {valid}")

                    if valid:
                        print(f"DEBUG-DOC: Valid file map generated")
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
            # For HTML-style comments (Markdown, HTML), use a special format that doesn't nest comments
            if start_multi == "<!--":
                formatted_map = f"{start_multi} FILE_MAP_BEGIN \n{start_multi}\n{file_map_json}\n{end_multi}\n{start_multi} FILE_MAP_END {end_multi}\n\n"
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

        print(f"DEBUG-DOC: Formatted file map: {formatted_map[:50]}...")

        # Save the current hash
        with open(hash_file, "w") as f:
            f.write(content_hash)
        print(f"DEBUG-DOC: Saved hash file")

        return formatted_map
