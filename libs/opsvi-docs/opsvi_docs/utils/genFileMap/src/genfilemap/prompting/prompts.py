# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Prompt Templates for Genfilemap","description":"This module provides prompt templates for different file types, using advanced reasoning methods to guide the LLM toward accurate results.","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary libraries and modules for the functionality of the prompts.","line_start":6,"line_end":12},{"name":"Default System Messages","description":"Defines default hardcoded system messages used as fallbacks if not configured.","line_start":14,"line_end":128},{"name":"Configuration Management","description":"Functions related to configuration management, including retrieval and initialization.","line_start":130,"line_end":135},{"name":"Code System Message Retrieval","description":"Function to retrieve the system message for code file processing.","line_start":135,"line_end":169},{"name":"Documentation System Message Retrieval","description":"Function to retrieve the system message for documentation file processing.","line_start":169,"line_end":222},{"name":"User Prompt Generation for Code","description":"Function to generate a user prompt for code file analysis.","line_start":222,"line_end":276}],"key_elements":[{"name":"_get_config","description":"Function to get the configuration instance, initializing it if needed.","line":130},{"name":"get_code_system_message","description":"Function to get the system message for code file processing.","line":135},{"name":"get_documentation_system_message","description":"Function to get the system message for documentation file processing.","line":169},{"name":"get_code_user_prompt","description":"Function to generate a user prompt for code file analysis.","line":222},{"name":"DEFAULT_CODE_SYSTEM_MESSAGE","description":"Default hardcoded system message for code processing.","line":14},{"name":"DEFAULT_DOCUMENTATION_SYSTEM_MESSAGE","description":"Default hardcoded system message for documentation processing.","line":128}]}
"""
# FILE_MAP_END

"""
Prompt templates for genfilemap.

This module provides prompt templates for different file types, using
advanced reasoning methods to guide the LLM toward accurate results.
"""

import json
from typing import Dict, Any

from genfilemap.config import Config

# Default hardcoded system messages - used as fallbacks if not configured
DEFAULT_CODE_SYSTEM_MESSAGE = """You are a specialized AI assistant for code analysis that creates structured file maps in JSON format.

Your task requires precise analysis using multi-step reasoning:

1) CAREFUL ANALYSIS: Examine the code file thoroughly to identify:
   - Key components (classes, functions, variables, imports)
   - Logical sections and their boundaries
   - Important interfaces and data structures
   - The file's overall purpose and architecture

2) STRUCTURED THINKING: Use a Tree of Thought approach to map the file:
   a) First identify all major sections and their line boundaries
   b) Then identify key elements within each section
   c) Verify line numbers by counting from the top of the file
   d) Double-check that all line ranges are accurate and non-overlapping

3) JSON GENERATION: Create a precisely structured JSON object following this exact schema:
```json
{
  "file_metadata": {
    "title": "Descriptive title of the file",
    "description": "Comprehensive description of the file's purpose and contents",
    "last_updated": "YYYY-MM-DD format date",
    "type": "file_type (e.g., code, documentation, configuration)"
  },
  "ai_instructions": "When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
  "sections": [
    {
      "name": "Section Name",
      "description": "Brief description of this section's purpose",
      "line_start": X, // integer line number where section starts
      "line_end": Y // integer line number where section ends
    },
    // Additional sections...
  ],
  "key_elements": [
    {
      "name": "Element Name",
      "description": "Brief description of this element",
      "line": Z // integer line number where this element is defined
    },
    // Additional key elements...
  ]
}
```

4) VERIFICATION: Validate your output with these checks:
   - All line numbers are accurate and within the file bounds
   - All required JSON fields are present and correctly formatted
   - Section descriptions correctly capture each section's purpose
   - Line ranges for sections are comprehensive and non-overlapping
   - The file metadata accurately reflects the file's purpose

IMPORTANT: Return ONLY the JSON object with no additional text, markdown formatting, or explanations. Your response must be valid, parseable JSON."""

DEFAULT_DOCUMENTATION_SYSTEM_MESSAGE = """You are a specialized AI assistant for documentation analysis that creates structured file maps in JSON format.

Your task requires precise analysis using multi-step reasoning:

1) DOCUMENTATION STRUCTURE ANALYSIS: Carefully examine the documentation to identify:
   - Main sections and their hierarchical relationships
   - Headings and subheadings with their exact line numbers
   - Key concepts, definitions, and examples
   - The document's overall purpose and audience

2) STRUCTURED MAPPING PROCESS: Use a Tree of Thought approach to map the document:
   a) First identify all major headers and their line numbers
   b) Group content under appropriate sections based on heading hierarchy
   c) Verify line numbers by counting from the top of the document
   d) Double-check that all section boundaries are accurate and complete

3) JSON GENERATION: Create a precisely structured JSON object following this exact schema:
```json
{
  "file_metadata": {
    "title": "Descriptive title of the document",
    "description": "Comprehensive description of the document's purpose and contents",
    "last_updated": "YYYY-MM-DD format date",
    "type": "file_type (e.g., documentation, tutorial, reference)"
  },
  "ai_instructions": "When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
  "sections": [
    {
      "name": "Section Name",
      "description": "Brief description of this section's purpose",
      "line_start": X, // integer line number where section starts
      "line_end": Y // integer line number where section ends
    },
    // Additional sections...
  ],
  "key_elements": [
    {
      "name": "Element Name",
      "description": "Brief description of this element",
      "line": Z // integer line number where this element is defined
    },
    // Additional key elements...
  ]
}
```

4) VERIFICATION: Validate your output with these checks:
   - All line numbers are accurate by counting from line 1
   - All required JSON fields are present and correctly formatted
   - Section boundaries correspond to actual section transitions
   - Line ranges for sections are comprehensive and non-overlapping
   - The file metadata accurately captures the document's purpose

IMPORTANT: Return ONLY the JSON object with no additional text, markdown formatting, or explanations. Your response must be valid, parseable JSON."""

# Global configuration instance - will be initialized when first needed
_config = None


def _get_config() -> Config:
    """Get the configuration instance, initializing it if needed"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def get_code_system_message() -> str:
    """
    Get the system message for code file processing.

    First checks for a configuration value following precedence order:
    1. Command-line arguments
    2. Environment variables
    3. Config file values

    Falls back to the hardcoded default if not found in any of the above.
    """
    config = _get_config()
    # Check for the message in the configuration following precedence order
    message = config.get("system_prompts.code_system_message")
    # Fall back to the default hardcoded message if not found in configuration
    return message or DEFAULT_CODE_SYSTEM_MESSAGE


def get_documentation_system_message() -> str:
    """
    Get the system message for documentation file processing.

    First checks for a configuration value following precedence order:
    1. Command-line arguments
    2. Environment variables
    3. Config file values

    Falls back to the hardcoded default if not found in any of the above.
    """
    config = _get_config()
    # Check for the message in the configuration following precedence order
    message = config.get("system_prompts.documentation_system_message")
    # Fall back to the default hardcoded message if not found in configuration
    return message or DEFAULT_DOCUMENTATION_SYSTEM_MESSAGE


def get_code_user_prompt(
    file_path: str,
    file_type: str,
    current_date: str,
    content: str,
    structure_analysis: Dict[str, Any],
) -> str:
    """
    Generate a user prompt for code file analysis.

    Args:
        file_path: Path to the file
        file_type: Type of the file (python, javascript, etc.)
        current_date: Current date in YYYY-MM-DD format
        content: The file content
        structure_analysis: Analysis of the file structure

    Returns:
        A prompt string tailored for code file analysis
    """
    # Format the structure analysis as a helpful guide for the LLM
    analysis_json = json.dumps(structure_analysis, indent=2)

    # Build the prompt with file info, pre-analysis results, and clear instructions
    prompt = f"""I'm going to analyze a code file and create a detailed file map for it.

FILE INFORMATION:
- Path: {file_path}
- Type: {file_type}
- Date: {current_date}
- Total Lines: {structure_analysis.get('line_count', 0)}

IMPORTANT NOTE ON LINE NUMBERS:
I've added two blank lines at the beginning of the content below. These represent where 
the file map will be inserted. Please include these blank lines when counting line numbers
for your analysis - this ensures the line numbers in your file map will be accurate when
the file map is inserted at the top of the document.

When identifying key elements, please locate the exact line where each variable, function, or class is DEFINED, not where it's used. For sections, ensure they represent complete logical blocks of code that serve a unified purpose - don't divide logical operations across multiple sections.

STRUCTURE ANALYSIS:
{analysis_json}

REASONING STEPS:
1. Analyze the file content to understand its structure and purpose
2. Identify major sections with their line boundaries
3. Identify key elements (functions, classes, etc.) with their line numbers
4. Count line numbers including the two blank lines at the top
5. Create JSON following the required schema
6. Verify all line numbers are accurate and sections are non-overlapping

"""

    # Add conditional prompt for complex files
    if len(structure_analysis.get("sections", [])) > 30:
        prompt += f"""
IMPORTANT: This file has {len(structure_analysis["sections"])} sections, which is too many for a detailed file map. 
Please generate a simplified, higher-level file map instead, following these guidelines:

- Group similar sections into larger logical sections
- Aim for no more than 10-15 high-level sections
- Focus on the overall structure rather than fine details
- Still include key elements, but only the most important ones
- Ensure the file map is still accurate and useful for navigating the file
"""

    prompt += f"""
FILE CONTENT:
{content}

I'll now generate a comprehensive, accurate file map JSON with precise line numbers that already account for the file map insertion at the top of the document.
"""

    return prompt


def get_documentation_user_prompt(
    file_path: str,
    file_type: str,
    current_date: str,
    content: str,
    structure_analysis: Dict[str, Any],
) -> str:
    """
    Generate a user prompt for documentation file analysis.

    Args:
        file_path: Path to the file
        file_type: Type of the file (markdown, etc.)
        current_date: Current date in YYYY-MM-DD format
        content: The file content
        structure_analysis: Analysis of the file structure

    Returns:
        A prompt string tailored for documentation file analysis
    """
    # Format the headings analysis as a helpful guide for the LLM
    headings = structure_analysis.get("headings", [])
    headings_text = ""
    if headings:
        headings_text = "Detected Headings:\n"
        for heading in headings:
            headings_text += f"- Level {heading['level']}: '{heading['text']}' at line {heading['line']}\n"

    # Build the prompt with file info, pre-analysis results, and clear instructions
    prompt = f"""I'm going to analyze a documentation file and create a detailed file map for it.

FILE INFORMATION:
- Path: {file_path}
- Type: {file_type}
- Date: {current_date}
- Total Lines: {structure_analysis.get('line_count', 0)}

IMPORTANT NOTE ON LINE NUMBERS:
I've added two blank lines at the beginning of the content below. These represent where 
the file map will be inserted. Please include these blank lines when counting line numbers
for your analysis - this ensures the line numbers in your file map will be accurate when
the file map is inserted at the top of the document.

DOCUMENT STRUCTURE:
{headings_text}

REASONING APPROACH:
1. Analyze the document to understand its structure and hierarchy
2. Map each heading to a section, identifying precise line boundaries
3. Identify key elements like examples, definitions, or diagrams
4. Count line numbers including the two blank lines at the top
5. Create JSON following the required schema
6. Verify all line numbers are accurate and sections are non-overlapping

"""

    # Add conditional prompt for complex files
    if len(structure_analysis.get("headings", [])) > 30:
        prompt += f"""
IMPORTANT: This document has {len(structure_analysis["headings"])} headings, which is too many for a detailed file map.
Please generate a simplified, higher-level file map instead, following these guidelines:

- Group related headings into larger logical sections 
- Aim for no more than 10-15 high-level sections
- Focus on the overall document structure rather than every subheading
- Still include key elements, but only the most important ones
- Ensure the file map is still accurate and useful for navigating the document
"""

    prompt += f"""
CONTENT:
{content}

I'll now generate a comprehensive, accurate file map JSON with precise line numbers that already account for the file map insertion at the top of the document.
"""

    return prompt
