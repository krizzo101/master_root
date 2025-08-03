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
from pathlib import Path

from genfilemap.processors.base import FileProcessor
from genfilemap.prompting.prompts import get_documentation_system_message, get_documentation_user_prompt
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
        heading_pattern = r'^(#{1,6})\s+(.+?)(?:\s*#{1,6})?$'

        lines = content.split('\n')
        for i, line in enumerate(lines):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    "level": level,
                    "text": text,
                    "line": i + 1  # 1-indexed line numbers
                })

        # Add heading information to the analysis
        analysis["headings"] = headings

        return analysis

    async def generate_file_map(self, content: str, comment_style: Tuple[str, str, str], force: bool = False) -> Optional[str]:
        """
        Generate a file map specialized for documentation files.

        Uses document structure analysis to guide the LLM in creating an accurate file map.

        Args:
            content: The file content to generate a map for
            comment_style: The comment style tuple (start_multi, end_multi, single_line)
            force: Whether to force generation even if hash matches
        """
        start_multi, end_multi, single_line = comment_style

        # Initialize pattern variables before use - moved outside of conditional blocks
        html_pattern = r"<!-- FILE_MAP_BEGIN\s*\n<!--\s*\n(.*?)\n\s*-->\s*\n<!-- FILE_MAP_END -->"
        legacy_html_pattern = r"<!-- FILE_MAP_BEGIN -->(?:\s*|\s+)<!--\s*(\{.*?\})\s*-->(?:\s*|\s+)<!-- FILE_MAP_END -->"
        generic_pattern = r"(?:\/\*|\<!--)\s*(\{.*?\})\s*(?:\*\/|\-->)"

        # Extract existing file map if it exists
        existing_map, remaining_content = extract_existing_file_map(content, comment_style)

        # Calculate hash of the content without the file map
        content_hash = calculate_file_hash(remaining_content)

        # Check if there's a stored hash for this file
        hash_file = f"{self.file_path}.hash"
        if not force and os.path.exists(hash_file):
            with open(hash_file, 'r') as f:
                stored_hash = f.read().strip()

            # If hash matches and we have an existing map, check if it's valid
            if stored_hash == content_hash and existing_map:
                # Try pattern for HTML-style comments first
                json_match = re.search(html_pattern, existing_map, re.DOTALL)

                # Try legacy HTML format
                if not json_match:
                    json_match = re.search(legacy_html_pattern, existing_map, re.DOTALL)

                # Try generic format
                if not json_match:
                    json_match = re.search(generic_pattern, existing_map, re.DOTALL)

                if json_match:
                    file_map_json = json_match.group(1).strip()
                    try:
                        # Try to parse the JSON first
                        json_obj = json.loads(file_map_json)
                        # Then validate the map structure
                        valid = await self.validate_generated_map(file_map_json, content)
                        if valid:
                            if force:
                                self.debug_print(f"DEBUG-DOC: Force flag is set, generating new file map anyway")
                            else:
                                self.debug_print(f"DEBUG-DOC: Existing map is valid, returning None to skip update")
                                return None  # Valid file map, no need to update
                    except json.JSONDecodeError as e:
                        self.debug_print(f"DEBUG-DOC: Invalid JSON in existing map: {str(e)}")
                else:
                    self.debug_print(f"DEBUG-DOC: No JSON found in existing map")
        else:
            if force:
                self.debug_print(f"DEBUG-DOC: Force flag is set, will generate new map regardless of hash")
            else:
                self.debug_print(f"DEBUG-DOC: No hash file found, will generate new map")

        # Get the current date
        current_date = datetime.now().strftime("%Y-%m-%d")

        # FIXED: Use the remaining content directly without artificial padding
        # Line numbers should be based on the actual content structure, not padded content
        # The FILE_MAP will be inserted at the top, but line numbers should reference
        # the actual content lines as they appear in the final file

        # Perform structure analysis on the remaining content (without FILE_MAP)
        structure_analysis = await self.analyze_structure(remaining_content)
        self.debug_print(f"DEBUG-DOC: Structure analysis completed with {len(structure_analysis.get('headings', []))} headings")

        # Calculate the offset that will be added by the FILE_MAP header
        # This offset will be applied to all line numbers in the generated FILE_MAP
        if start_multi == "<!--":
            # HTML-style comments typically use 5-6 lines for FILE_MAP + 1 blank line
            file_map_offset = 6
        else:
            # Other comment styles typically use 2-3 lines + 1 blank line
            file_map_offset = 3

        self.debug_print(f"DEBUG-DOC: Calculated FILE_MAP offset: {file_map_offset} lines")

        # Get config for max headings
        config = {"processors.documentation.max_headings": 30}  # Default value
        if hasattr(self, "config"):
            config = self.config

        # Get messages for LLM
        system_message = get_documentation_system_message()
        user_prompt = get_documentation_user_prompt(
            file_path=self.file_path,
            file_type=self.file_type,
            current_date=current_date,
            content=remaining_content,  # Use the actual content without FILE_MAP
            structure_analysis=structure_analysis,
            config=config
        )

        # Generate with exponential backoff for rate limits
        max_retries = 3
        base_delay = 1
        file_map_json = None

        self.debug_print(f"DEBUG-DOC: Starting LLM generation with {max_retries} max retries")
        for attempt in range(max_retries):
            try:
                self.debug_print(f"DEBUG-DOC: LLM generation attempt {attempt+1}")
                result = await self.api_client.generate_completion(system_message, user_prompt, self.model)

                # Check if the response is an error message
                if result.startswith("ERROR:"):
                    self.debug_print(f"DEBUG-DOC: API error reported: {result}")
                    # If this is the last attempt, try fallback
                    if attempt == max_retries - 1:
                        self.debug_print(f"DEBUG-DOC: All standard attempts failed due to API errors, trying fallback generation")
                        fallback_json = await self.fallback_generation(
                            system_message=system_message,
                            user_prompt=user_prompt,
                            content=content,
                            comment_style=comment_style,
                            complexity_ratio=0.5
                        )

                        if fallback_json:
                            self.debug_print(f"DEBUG-DOC: Fallback generation succeeded")
                            file_map_json = fallback_json
                            break
                        else:
                            self.debug_print(f"DEBUG-DOC: Fallback generation also failed")
                            raise ValueError(f"Failed to generate valid file map JSON due to API error: {result}")

                    # Add exponential backoff delay and retry
                    delay = base_delay * (2 ** attempt)
                    self.debug_print(f"API error. Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                    continue

                # Log the raw response content for debugging
                self.debug_print(f"DEBUG-DOC-RAW-RESPONSE-START")
                self.debug_print(f"{result}")
                self.debug_print(f"DEBUG-DOC-RAW-RESPONSE-END")

                # Try to parse as JSON
                try:
                    file_map_obj = json.loads(result)

                    # FIXED: Apply the FILE_MAP offset to all line numbers
                    # The AI generated line numbers based on remaining_content (starting at line 1)
                    # but we need to adjust them to account for the FILE_MAP header
                    self.debug_print(f"DEBUG-DOC: Applying FILE_MAP offset of {file_map_offset} lines to all line numbers")

                    # Adjust section line numbers
                    for section in file_map_obj.get("sections", []):
                        if "line_start" in section:
                            section["line_start"] += file_map_offset
                        if "line_end" in section:
                            section["line_end"] += file_map_offset

                    # Adjust key element line numbers
                    for element in file_map_obj.get("key_elements", []):
                        if "line" in element:
                            element["line"] += file_map_offset

                    self.debug_print(f"DEBUG-DOC: Line number offset applied successfully")

                    # Validate against our schema
                    valid = await self.validate_generated_map(json.dumps(file_map_obj), content)
                    self.debug_print(f"DEBUG-DOC: Map validation result: {valid}")

                    if valid:
                        self.debug_print(f"DEBUG-DOC: Valid file map generated")
                        # Single-line JSON formatting - most compact representation
                        file_map_json = json.dumps(file_map_obj, separators=(',', ':'))
                        break
                    else:
                        self.debug_print(f"Generated file map failed validation for {self.file_path} (attempt {attempt+1})")
                        # If we've tried the maximum number of times and still failed, raise an exception
                        if attempt == max_retries - 1:
                            raise ValueError(f"Failed to generate valid file map after {max_retries} attempts - validation failed")
                except (json.JSONDecodeError, ValueError) as e:
                    self.debug_print(f"Invalid JSON response from LLM (attempt {attempt+1}): {str(e)}")
                    if attempt == max_retries - 1:
                        # Try fallback generation with reduced complexity
                        self.debug_print(f"DEBUG-DOC: All standard attempts failed, trying fallback generation")
                        fallback_json = await self.fallback_generation(
                            system_message=system_message,
                            user_prompt=user_prompt,
                            content=content,
                            comment_style=comment_style,
                            complexity_ratio=0.5
                        )

                        if fallback_json:
                            self.debug_print(f"DEBUG-DOC: Fallback generation succeeded")
                            file_map_json = fallback_json
                            break
                        else:
                            self.debug_print(f"DEBUG-DOC: Fallback generation also failed")
                            raise ValueError(f"Failed to generate valid file map JSON after {max_retries} attempts and fallback")
            except Exception as e:
                if attempt == max_retries - 1:
                    # Try fallback generation before giving up completely
                    self.debug_print(f"DEBUG-DOC: Error in API call, trying fallback generation: {str(e)}")
                    fallback_json = await self.fallback_generation(
                        system_message=system_message,
                        user_prompt=user_prompt,
                        content=content,
                        comment_style=comment_style,
                        complexity_ratio=0.5
                    )

                    if fallback_json:
                        self.debug_print(f"DEBUG-DOC: Fallback generation succeeded after API error")
                        file_map_json = fallback_json
                        break
                    else:
                        self.debug_print(f"DEBUG-DOC: Fallback generation also failed after API error")
                        raise e
                delay = base_delay * (2 ** attempt)
                self.debug_print(f"API error. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)

        # If we couldn't generate a valid file map, return None
        if not file_map_json:
            return None

        # Format the file map with the appropriate comment style
        if start_multi and end_multi:
            # For HTML-style comments (Markdown, HTML), use a special format that doesn't nest comments
            if start_multi == "<!--":
                formatted_map = f"{start_multi} FILE_MAP_BEGIN \n{start_multi}\n{file_map_json}\n{end_multi}\n{start_multi} FILE_MAP_END {end_multi}\n\n"
            # Special format for JavaScript, TypeScript, and CSS to avoid nested comment markers
            elif start_multi == "/*" and (ext := Path(self.file_path).suffix.lower()) in [".js", ".ts", ".jsx", ".tsx", ".css"]:
                formatted_map = f"{start_multi} FILE_MAP_BEGIN\n{file_map_json}\n{end_multi} {single_line} FILE_MAP_END\n\n"
                self.debug_print(f"DEBUG-DOC: Using {ext}-compatible file map format without nested comments")
            else:
                # Use multi-line comment style for other file types
                formatted_map = f"{start_multi} FILE_MAP_BEGIN {start_multi} {file_map_json} {end_multi} {end_multi} FILE_MAP_END {end_multi}\n\n"
        elif single_line:
            # Fall back to single-line comments if needed
            formatted_map = f"{single_line}FILE_MAP_BEGIN {single_line} {file_map_json} {single_line} FILE_MAP_END\n\n"
        else:
            # Use generic comment style as a last resort
            formatted_map = f"/* FILE_MAP_BEGIN */ /* {file_map_json} */ /* FILE_MAP_END */\n\n"

        self.debug_print(f"DEBUG-DOC: Formatted file map: {formatted_map[:50]}...")

        # Save the current hash
        with open(hash_file, 'w') as f:
            f.write(content_hash)
        self.debug_print(f"DEBUG-DOC: Saved hash file")

        return formatted_map

    async def fallback_generation(
        self,
        system_message: str,
        user_prompt: str,
        content: str,
        comment_style: Tuple[str, str, str],
        complexity_ratio: float = 0.5,
    ) -> Optional[str]:
        """
        Override fallback generation to apply FILE_MAP line number offset for documentation files.

        This ensures that even fallback generation produces correct line numbers.
        """
        # Calculate the same offset used in main generation
        start_multi, end_multi, single_line = comment_style
        if start_multi == "<!--":
            file_map_offset = 6  # HTML-style comments
        else:
            file_map_offset = 3  # Other comment styles

        self.debug_print(f"DEBUG-DOC-FALLBACK: Using FILE_MAP offset: {file_map_offset} lines")

        # Call the parent fallback generation
        fallback_result = await super().fallback_generation(
            system_message, user_prompt, content, comment_style, complexity_ratio
        )

        # If fallback succeeded, apply the line number offset
        if fallback_result:
            try:
                file_map_obj = json.loads(fallback_result)

                # Apply the same offset logic as in main generation
                self.debug_print(f"DEBUG-DOC-FALLBACK: Applying FILE_MAP offset to fallback result")

                # Adjust section line numbers
                for section in file_map_obj.get("sections", []):
                    if "line_start" in section:
                        section["line_start"] += file_map_offset
                    if "line_end" in section:
                        section["line_end"] += file_map_offset

                # Adjust key element line numbers
                for element in file_map_obj.get("key_elements", []):
                    if "line" in element:
                        element["line"] += file_map_offset

                self.debug_print(f"DEBUG-DOC-FALLBACK: Line number offset applied to fallback result")

                # Return the corrected JSON
                return json.dumps(file_map_obj, separators=(',', ':'))

            except (json.JSONDecodeError, KeyError) as e:
                self.debug_print(f"DEBUG-DOC-FALLBACK: Error applying offset to fallback result: {str(e)}")
                # Return the original result if we can't parse/modify it
                return fallback_result

        return fallback_result