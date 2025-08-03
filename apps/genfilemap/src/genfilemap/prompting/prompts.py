"""
Prompt templates for GenFileMap.

This module provides prompt templates for different file types, using
advanced reasoning methods to guide the LLM toward accurate results.
"""

import json
import os
from typing import Dict, Any, Optional

from genfilemap.config import load_config, get_config_value

# Default hardcoded system messages - used as fallbacks if not configured
DEFAULT_CODE_SYSTEM_MESSAGE = """# Role and Objective
You are a specialized AI assistant for code analysis that creates structured file maps in JSON format. Your primary objective is to analyze code files thoroughly and generate accurate, comprehensive file maps that enable efficient navigation and understanding.

# Instructions

## Core Analysis Requirements
- Examine code files systematically to identify all key components, logical sections, and structural elements
- Generate precise JSON file maps that accurately represent the file's organization
- Ensure all line numbers are accurate and verified through careful counting
- Focus on creating actionable navigation aids for both humans and AI systems

## Analysis Methodology
You MUST follow this systematic approach:

1. **Initial File Scan**: Read through the entire file to understand its overall purpose and structure
2. **Component Identification**: Identify all significant elements (classes, functions, imports, constants, interfaces)
3. **Section Mapping**: Determine logical divisions and their precise line boundaries
4. **Line Number Verification**: Count line numbers carefully from the top of the file (1-indexed)
5. **Quality Validation**: Verify that all sections are non-overlapping and accurately positioned

## JSON Schema Requirements
Generate a precisely structured JSON object following this EXACT schema:

```json
{
  "file_metadata": {
    "title": "Descriptive title summarizing the file's purpose",
    "description": "Comprehensive description of functionality and role in the project",
    "last_updated": "YYYY-MM-DD",
    "type": "code"
  },
  "ai_instructions": "Specific guidance for AI systems analyzing this file",
  "sections": [
    {
      "name": "Clear section identifier",
      "description": "Concise explanation of section purpose",
      "line_start": 1,
      "line_end": 10
    }
  ],
  "key_elements": [
    {
      "name": "Element identifier",
      "description": "Brief explanation of element purpose",
      "line": 5
    }
  ],
  "code_elements": {
    "functions": [
      {
        "name": "function_name",
        "signature": "complete function signature",
        "parameters": ["param1", "param2"],
        "return_type": "return type if available",
        "line": 15,
        "description": "function purpose and behavior"
      }
    ],
    "classes": [
      {
        "name": "ClassName",
        "inheritance": ["BaseClass"],
        "line": 25,
        "description": "class purpose and role"
      }
    ],
    "imports": [
      {
        "statement": "import statement exactly as written",
        "line": 1,
        "type": "import type (standard/third-party/local)"
      }
    ],
    "constants": [
      {
        "name": "CONSTANT_NAME",
        "value": "string representation of value",
        "line": 8,
        "description": "constant purpose"
      }
    ]
  }
}
```

# Critical Requirements

## Accuracy Standards
- All line numbers MUST be precisely calculated and verified
- Sections MUST NOT overlap in their line ranges
- All code elements MUST exist in the actual file content
- JSON output MUST be valid and well-formed

## Content Precision
- Use ONLY elements that actually exist in the provided code
- Do NOT invent, modify, or omit any structural elements
- Maintain exact parameter names, types, and signatures as written
- Represent constant values as strings regardless of their native type

## Formatting Standards
- Use clear, descriptive names for all sections and elements
- Keep descriptions concise but informative
- Ensure proper JSON syntax with correct escaping
- Follow consistent naming conventions throughout

# Output Requirements
Return ONLY the JSON object with no additional text, explanations, or formatting markers. The response must be pure, valid JSON that can be parsed directly."""

# Global configuration dictionary
_config = None


def _get_config() -> Dict[str, Any]:
    """Get configuration dictionary, initializing if necessary"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_code_system_message() -> str:
    """Get the system message for code file processing"""
    return f"""# Role and Objective
You are an expert code file structure analyzer specializing in creating comprehensive, accurate file maps. Your primary mission is to analyze code files systematically and generate structured JSON representations that enable efficient navigation and understanding for both humans and AI systems.

# Core Instructions

## Analysis Methodology
You MUST follow this systematic reasoning approach:

1. **Deep File Understanding**: Thoroughly examine the entire file to comprehend its purpose, architecture, and role within the project
2. **Structural Analysis**: Identify and categorize all significant components including classes, functions, imports, constants, and logical groupings
3. **Precision Mapping**: Create accurate line-based references for every element and section
4. **Quality Assurance**: Verify that all line numbers are correct and sections are properly bounded

## Chain of Thought Process
For each file analysis, think step by step:

1. **Initial Assessment**: What is this file's primary purpose and type?
2. **Component Discovery**: What are the major structural elements present?
3. **Section Identification**: How can the file be logically divided into navigable sections?
4. **Element Cataloging**: What specific functions, classes, and other key elements exist?
5. **Line Number Validation**: Are all line references accurate and verified?

# Output Requirements

## JSON Structure - CRITICAL SCHEMA COMPLIANCE
Generate a precisely formatted JSON object with these REQUIRED components:

```json
{{
  "file_metadata": {{
    "title": "string",
    "description": "string",
    "last_updated": "YYYY-MM-DD",
    "type": "string"
  }},
  "ai_instructions": "STRING - NOT an object! Must be a single string with guidance",
  "sections": [
    {{
      "name": "string",
      "description": "string - REQUIRED for every section",
      "line_start": integer,
      "line_end": integer
    }}
  ],
  "key_elements": [
    {{
      "name": "string",
      "description": "string - REQUIRED for every key element",
      "line": integer
    }}
  ],
  "code_elements": {{
    "functions": [...],
    "classes": [...],
    "imports": [...],
    "constants": [...]
  }}
}}
```

## CRITICAL SCHEMA REQUIREMENTS
- **ai_instructions**: MUST be a single string, NOT an object with {{"description": "..."}}
- **sections**: Every section MUST have name, description, line_start, line_end
- **key_elements**: Every key element MUST have name, description, line
- **No missing required fields**: All required fields must be present

## Quality Standards
- All line numbers MUST be 1-indexed and precisely calculated
- Sections MUST NOT overlap in their line ranges
- Extract detailed information including function signatures, parameters, return types, and class hierarchies
- Use ONLY elements that actually exist in the provided code
- Maintain exact parameter names, types, and signatures as written in the source
- Represent all constant values as strings regardless of their native data type

## Critical Instructions
- Ensure JSON output is valid and well-formed
- Use clear, descriptive names and concise but informative descriptions
- Structure the JSON with proper hierarchy and consistent naming conventions
- Do NOT invent fictional elements or modify existing code structure
- Focus on accuracy over completeness when in doubt

# Output Format
Return ONLY the JSON object with no additional text, explanations, or markdown formatting. The response must be pure, parseable JSON."""


def get_documentation_system_message() -> str:
    """
    Get the system message for documentation file processing optimized for GPT-4.1.

    Order of precedence for getting the system message:
    1. Config file values
    2. Hardcoded GPT-4.1 optimized default
    3. Environment variables

    Returns:
        str: The system message to use for documentation files
    """
    # Get from config if available
    config = _get_config()
    custom_message = get_config_value(config, "prompts.documentation_system_message")

    if custom_message:
        return custom_message

    # Return GPT-4.1 optimized default
    return """# Role and Objective
You are a specialized documentation analysis expert focused on creating structured file maps for documentation files. Your primary objective is to analyze documentation systematically and generate accurate JSON representations that enable efficient navigation and comprehension.

# Core Instructions

## Documentation Analysis Methodology
You MUST follow this systematic approach:

1. **Document Structure Assessment**: Examine the overall organization, heading hierarchy, and logical flow
2. **Content Categorization**: Identify different types of content (instructions, examples, references, etc.)
3. **Section Mapping**: Determine logical divisions based on headings, topics, and content boundaries
4. **Element Identification**: Locate key components like code blocks, tables, links, and important concepts
5. **Line Precision**: Ensure all line numbers are accurate and sections are properly bounded

## Chain of Thought Process
For each documentation file, reason through:

1. **Purpose Identification**: What is this document's primary goal and audience?
2. **Structure Analysis**: How is the content organized and what is the heading hierarchy?
3. **Content Mapping**: What are the main topics and how do they relate?
4. **Navigation Points**: What are the most important sections and elements for quick reference?
5. **Context Understanding**: How does this document fit within the larger project or system?

# Output Requirements

## JSON Structure
Generate a precisely formatted JSON object with these components:

- **file_metadata**: Document information (title, description, last_updated, type)
- **ai_instructions**: MUST be a single string (NOT an object) with specific guidance for AI systems
- **sections**: Logical document divisions with exact line ranges (non-overlapping) - EVERY section MUST have a description
- **key_elements**: Important components like code blocks, tables, or critical concepts - EVERY element MUST have a description

## CRITICAL SCHEMA REQUIREMENTS
- **ai_instructions**: Must be a plain string, not an object with {{"description": "..."}}
- **sections**: Every section MUST include: name, description, line_start, line_end
- **key_elements**: Every key element MUST include: name, description, line
- **NO MISSING FIELDS**: All required fields must be present or validation will fail

## Quality Standards
- All line numbers MUST be 1-indexed and precisely calculated
- Sections MUST NOT overlap in their line ranges
- Focus on creating navigable, logical sections based on content themes
- Capture important elements that aid in document comprehension
- Use clear, descriptive names that reflect the actual content

## Critical Instructions
- Ensure JSON output is valid and well-formed
- Prioritize accuracy over completeness when determining line boundaries
- Create sections that genuinely reflect the document's logical organization
- Use descriptive but concise section names and descriptions
- Account for any blank lines or formatting in line number calculations

# Output Format
Return ONLY the JSON object with no additional text, explanations, or markdown formatting. The response must be pure, parseable JSON."""


def get_code_user_prompt(
    file_path: str = None,
    file_type: str = None,
    current_date: str = None,
    content: str = None,
    structure_analysis: Dict[str, Any] = None,
    config: Dict[str, Any] = None,
) -> str:
    """
    Generate a user prompt for code file analysis with GPT-4.1 optimization.

    Args:
        file_path: Path to the file being analyzed
        file_type: Type/extension of the file
        current_date: Current date in YYYY-MM-DD format
        content: The actual file content to analyze
        structure_analysis: Pre-computed analysis of file structure
        config: Configuration dictionary

    Returns:
        A GPT-4.1 optimized prompt string for code file analysis
    """
    # Set defaults
    file_path = file_path or "unknown_file"
    file_type = file_type or "code"
    current_date = current_date or "2024-01-01"
    content = content or ""
    structure_analysis = structure_analysis or {}
    config = config or {}

    # Extract file information
    file_name = os.path.basename(file_path) if file_path else "unknown_file"
    file_extension = os.path.splitext(file_name)[1] if file_name else ""

    # Language-specific instructions
    language_guidance = ""
    if file_extension.lower() in [".py", ".python"]:
        language_guidance = """
## Python-Specific Analysis
- Pay special attention to class definitions and inheritance hierarchies
- Identify decorator usage and async/await patterns
- Capture import statements with their types (standard/third-party/local)
- Note function signatures including type hints if present
- Identify constants following Python naming conventions (UPPER_CASE)
"""
    elif file_extension.lower() in [".js", ".ts", ".jsx", ".tsx"]:
        language_guidance = """
## JavaScript/TypeScript Analysis
- Identify function declarations, arrow functions, and class definitions
- Note import/export statements and module patterns
- Capture type definitions for TypeScript files
- Identify React components and hooks if applicable
- Note async/await and Promise patterns
"""
    elif file_extension.lower() in [".java", ".kt"]:
        language_guidance = """
## Java/Kotlin Analysis
- Identify package declarations and import statements
- Note class definitions with access modifiers and inheritance
- Capture method signatures with return types and parameters
- Identify interface definitions and implementations
- Note annotation usage and static members
"""

    # Extract key information from analysis
    code_elements = structure_analysis.get("code_elements", {})
    function_count = len(code_elements.get("functions", []))
    class_count = len(code_elements.get("classes", []))
    import_count = len(code_elements.get("imports", []))
    constant_count = len(code_elements.get("constants", []))

    content_summary = f"""
## File Analysis Summary
- File contains {function_count} functions/methods
- Contains {class_count} classes/types
- Has {import_count} import statements
- Includes {constant_count} constants/variables
- File type: {file_type}
- Extension: {file_extension}
"""

    # Generate code elements instruction with verified data
    code_elements_json = json.dumps(code_elements, indent=2)

    code_elements_instruction = (
        """
## Pre-Analyzed Code Elements
CRITICAL: Use EXACTLY these code elements from the structural analysis. Do NOT modify, add, or remove any elements.

```json
"""
        + code_elements_json
        + """
```

These elements have been verified to exist in the file. Your task is to organize them into the proper JSON structure."""
    )

    return f"""# Analysis Task
Analyze the following {file_type} file and create a comprehensive file map using systematic reasoning.

## File Information
- **File Path**: {file_path}
- **File Name**: {file_name}
- **Date**: {current_date}
{content_summary}

{language_guidance}

# Reasoning Strategy
Follow this step-by-step approach:

1. **File Purpose Analysis**: Examine the file to understand its primary role and functionality within the project
2. **Structural Decomposition**: Identify logical sections that group related functionality
3. **Element Cataloging**: Use the provided code elements to populate the detailed analysis
4. **Line Number Verification**: Ensure all line numbers are accurate through careful counting
5. **Quality Validation**: Verify sections don't overlap and all references are correct

{code_elements_instruction}

# Output Requirements

Generate a valid JSON object with these exact components:

- **file_metadata**: Include title, description, last_updated ({current_date}), and type
- **ai_instructions**: MUST be a single string (NOT an object) with guidance for AI systems
- **sections**: Logical divisions with precise line_start and line_end values - EVERY section MUST have a description
- **key_elements**: Important individual components with exact line numbers - EVERY element MUST have a description
- **code_elements**: Use the exact structure provided above

## CRITICAL SCHEMA COMPLIANCE
- **ai_instructions**: Must be a plain string, not an object with {{"description": "..."}}
- **sections**: Every section MUST include: name, description, line_start, line_end
- **key_elements**: Every key element MUST include: name, description, line
- **NO MISSING FIELDS**: All required fields must be present or validation will fail

## Critical Instructions
- All line numbers MUST be 1-indexed and precisely calculated
- Sections MUST NOT overlap in their line ranges
- For imports, use field name 'statement' (not 'import_statement')
- For constants, represent all values as strings regardless of native type
- For class inheritance, always use array format even for single inheritance
- Use ONLY the elements provided in the pre-analyzed code elements section

## File Content to Analyze
```
{content}
```

Think through each step systematically, then provide ONLY the final JSON object with no additional text or explanation."""


def get_documentation_user_prompt(
    file_path: str,
    file_type: str,
    current_date: str,
    content: str,
    structure_analysis: Dict[str, Any],
    config=None,
) -> str:
    """
    Generate a GPT-4.1 optimized user prompt for documentation file analysis.

    Args:
        file_path: Path to the file
        file_type: Type of the file (markdown, etc.)
        current_date: Current date in YYYY-MM-DD format
        content: The file content
        structure_analysis: Analysis of the file structure
        config: Optional configuration object

    Returns:
        A GPT-4.1 optimized prompt string tailored for documentation file analysis
    """
    # Default config if none provided
    config = config or {}

    # Extract file information
    file_name = os.path.basename(file_path)

    # Format the headings analysis as guidance for the LLM
    headings = structure_analysis.get("headings", [])
    headings_analysis = ""
    if headings:
        headings_analysis = "## Detected Document Structure\n"
        for heading in headings:
            indent = "  " * (heading["level"] - 1)
            headings_analysis += f"{indent}- Level {heading['level']}: '{heading['text']}' (line {heading['line']})\n"
        headings_analysis += f"\nTotal headings detected: {len(headings)}"

    # Determine complexity and provide appropriate guidance
    max_headings = get_config_value(config, "processors.documentation.max_headings", 30)
    complexity_guidance = ""

    if len(headings) > max_headings:
        complexity_guidance = f"""
## Complexity Management
IMPORTANT: This document contains {len(headings)} headings, which exceeds the recommended maximum of {max_headings}.

Apply this simplified analysis strategy:
- Group related headings into larger logical sections (aim for 10-15 high-level sections)
- Focus on major document divisions rather than every subheading
- Prioritize structural organization over granular detail
- Still capture key elements, but only the most important navigation points
- Ensure the file map remains useful for document navigation while being manageable
"""
    else:
        complexity_guidance = """
## Standard Analysis
- Create detailed sections based on the document structure
- Include all major headings as separate sections where logical
- Capture important subsections that aid navigation
- Identify key elements like code blocks, tables, and important concepts
"""

    return f"""# Documentation Analysis Task
Analyze this {file_type} documentation file and create a comprehensive file map using systematic reasoning.

## File Information
- **File Path**: {file_path}
- **File Name**: {file_name}
- **Date**: {current_date}
- **File Type**: {file_type}

{headings_analysis}

{complexity_guidance}

# Reasoning Strategy
Follow this step-by-step analytical approach:

1. **Document Purpose Analysis**:
   - What is the primary purpose of this document?
   - Who is the intended audience?
   - How does it fit within the larger project context?

2. **Structural Understanding**:
   - Examine the heading hierarchy and document organization
   - Identify major topics and their relationships
   - Determine logical section boundaries

3. **Content Categorization**:
   - Distinguish between instructional content, examples, references, and explanations
   - Identify important code blocks, tables, diagrams, or special formatting
   - Note cross-references and links to other documents

4. **Navigation Optimization**:
   - Create sections that facilitate efficient document navigation
   - Ensure section boundaries align with content themes
   - Verify line numbers account for all formatting and blank lines

5. **Quality Validation**:
   - Confirm all line numbers are accurate and sections don't overlap
   - Verify section names accurately reflect their content
   - Ensure the file map enhances rather than duplicates the document structure

# Critical Analysis Requirements

## Line Number Precision
- Count ALL lines including blank lines, headers, and formatting
- Use 1-indexed counting (first line = 1)
- Account for the file map insertion when calculating final positions
- Ensure sections have logical start and end boundaries

## Section Creation Guidelines
- Base sections on content themes and logical divisions
- Use heading structure as guidance but don't create a section for every heading
- Group related subsections under broader themes when appropriate
- Ensure each section has a clear, descriptive name and purpose

## Key Elements Identification
- Code blocks and their purposes
- Important tables, lists, or data structures
- Cross-references and external links
- Warning callouts, examples, or special formatting
- Concepts or terms that are central to understanding

# Output Requirements

Generate a valid JSON object with exactly these components:

- **file_metadata**: title, description, last_updated ({current_date}), type ("documentation")
- **ai_instructions**: MUST be a single string (NOT an object) with specific guidance for AI systems
- **sections**: Logical document divisions with accurate line_start and line_end - EVERY section MUST have a description
- **key_elements**: Important navigation points and content elements - EVERY element MUST have a description

## CRITICAL SCHEMA COMPLIANCE
- **ai_instructions**: Must be a plain string, not an object with {{"description": "..."}}
- **sections**: Every section MUST include: name, description, line_start, line_end
- **key_elements**: Every key element MUST include: name, description, line
- **NO MISSING FIELDS**: All required fields must be present or validation will fail

## Critical Instructions
- All line numbers MUST be 1-indexed and precisely calculated
- Sections MUST NOT overlap in their line ranges
- Create logical, navigable sections that reflect the document's true organization
- Use clear, descriptive names that indicate the section's content and purpose
- Focus on creating a useful navigation aid, not just a structural copy

## Document Content
```
{content}
```

Think through the analysis systematically using the reasoning strategy above, then provide ONLY the final JSON object with no additional text or explanation."""
