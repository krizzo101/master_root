# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Markdown Parser Module","description":"This module provides functions to parse markdown files from the documentation standards and extract structured content from them.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation for the markdown parser module.","line_start":3,"line_end":7},{"name":"Imports","description":"Import statements for required modules.","line_start":8,"line_end":12},{"name":"Logging Configuration","description":"Configuration for logging within the module.","line_start":13,"line_end":16},{"name":"parse_markdown_file Function","description":"Function to parse a markdown file and extract its structured content.","line_start":18,"line_end":56},{"name":"extract_title Function","description":"Function to extract the title from markdown content.","line_start":58,"line_end":72},{"name":"extract_sections Function","description":"Function to extract sections from markdown content based on headings.","line_start":74,"line_end":122},{"name":"process_subsections Function","description":"Function to organize sections into a hierarchical structure based on heading levels.","line_start":124,"line_end":134},{"name":"extract_examples Function","description":"Function to extract examples from markdown content.","line_start":136,"line_end":153},{"name":"extract_code_blocks Function","description":"Function to extract code blocks from markdown content.","line_start":155,"line_end":175},{"name":"extract_lists Function","description":"Function to extract lists from markdown content.","line_start":177,"line_end":208},{"name":"extract_tables Function","description":"Function to extract tables from markdown content.","line_start":210,"line_end":241},{"name":"extract_images Function","description":"Function to extract images from markdown content.","line_start":243,"line_end":260}],"key_elements":[{"name":"parse_markdown_file","description":"Function to parse a markdown file and extract its structured content.","line":20},{"name":"extract_title","description":"Function to extract the title from markdown content.","line":57},{"name":"extract_sections","description":"Function to extract sections from markdown content based on headings.","line":73},{"name":"process_subsections","description":"Function to organize sections into a hierarchical structure based on heading levels.","line":123},{"name":"extract_examples","description":"Function to extract examples from markdown content.","line":135},{"name":"extract_code_blocks","description":"Function to extract code blocks from markdown content.","line":154},{"name":"extract_lists","description":"Function to extract lists from markdown content.","line":176},{"name":"extract_tables","description":"Function to extract tables from markdown content.","line":209},{"name":"extract_images","description":"Function to extract images from markdown content.","line":242},{"name":"re","description":"Regular expression module used for pattern matching.","line":8},{"name":"Dict","description":"Type hint for dictionaries used in function signatures.","line":9},{"name":"List","description":"Type hint for lists used in function signatures.","line":9},{"name":"Any","description":"Type hint for any type used in function signatures.","line":9},{"name":"Optional","description":"Type hint for optional types used in function signatures.","line":9},{"name":"Tuple","description":"Type hint for tuples used in function signatures.","line":9},{"name":"os","description":"Operating system interface module used for file path operations.","line":10},{"name":"logging","description":"Logging module used for logging errors and information.","line":11}]}
"""
# FILE_MAP_END

"""
Markdown Parser Module for Documentation Rule Generator.

This module provides functions to parse markdown files from the documentation standards
and extract structured content from them.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_markdown_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a markdown file and extract its structured content.

    Args:
        file_path: Path to the markdown file

    Returns:
        A dictionary containing the parsed content
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return {"error": f"File not found: {file_path}"}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract basic metadata
        result = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "title": extract_title(content),
            "sections": extract_sections(content),
            "examples": extract_examples(content),
            "code_blocks": extract_code_blocks(content),
            "lists": extract_lists(content),
            "tables": extract_tables(content),
            "images": extract_images(content),
        }

        return result
    except Exception as e:
        logger.error(f"Error parsing markdown file {file_path}: {str(e)}")
        return {"error": str(e)}


def extract_title(content: str) -> str:
    """
    Extract the title (first h1) from the markdown content.

    Args:
        content: Markdown content

    Returns:
        The title of the document
    """
    title_match = re.search(r"^# (.*?)$", content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    return "Untitled Document"


def extract_sections(content: str) -> Dict[str, Any]:
    """
    Extract sections from the markdown content based on headings.

    Args:
        content: Markdown content

    Returns:
        Dictionary of sections with their content
    """
    sections = {}

    # Find all headings and their content
    heading_pattern = r"^(#{2,6}) (.*?)$"
    headings = re.finditer(heading_pattern, content, re.MULTILINE)

    heading_positions = []
    for match in headings:
        level = len(match.group(1))
        title = match.group(2).strip()
        position = match.start()
        heading_positions.append((level, title, position))

    # Add the end of file as a final position
    heading_positions.append((0, "EOF", len(content)))

    # Extract content between headings
    for i in range(len(heading_positions) - 1):
        level, title, position = heading_positions[i]
        next_position = heading_positions[i + 1][2]

        # Get content between this heading and the next one
        section_content = content[position:next_position].strip()
        # Remove the heading itself from the content
        section_content = re.sub(
            r"^#{2,6} .*?$", "", section_content, 1, re.MULTILINE
        ).strip()

        sections[title] = {
            "level": level,
            "content": section_content,
            "subsections": {},
        }

    # Process subsections
    process_subsections(sections)

    return sections


def process_subsections(sections: Dict[str, Any]) -> None:
    """
    Organize sections into a hierarchical structure based on heading levels.

    Args:
        sections: Dictionary of sections
    """
    # This is a placeholder for more complex subsection processing
    # In a full implementation, this would organize sections into a proper hierarchy
    pass


def extract_examples(content: str) -> List[Dict[str, str]]:
    """
    Extract examples from the markdown content.

    Args:
        content: Markdown content

    Returns:
        List of examples with their content
    """
    examples = []
    example_pattern = r"<example>\s*(.*?)\s*</example>"

    for match in re.finditer(example_pattern, content, re.DOTALL):
        examples.append({"content": match.group(1).strip()})

    return examples


def extract_code_blocks(content: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from the markdown content.

    Args:
        content: Markdown content

    Returns:
        List of code blocks with language and content
    """
    code_blocks = []
    # Match code blocks with language specification
    code_pattern = r"```([\w+-]*)\s*(.*?)```"

    for match in re.finditer(code_pattern, content, re.DOTALL):
        language = match.group(1).strip() or "text"
        code_content = match.group(2).strip()
        code_blocks.append({"language": language, "content": code_content})

    return code_blocks


def extract_lists(content: str) -> List[Dict[str, Any]]:
    """
    Extract lists from the markdown content.

    Args:
        content: Markdown content

    Returns:
        List of lists with their items
    """
    lists = []
    # First find potential list regions
    list_regions = re.finditer(
        r"(?:^|\n)(?:[\*\-\+]|\d+\.)\s+.*(?:\n(?:[\*\-\+]|\d+\.)\s+.*)*", content
    )

    for region in list_regions:
        list_content = region.group(0)
        items = re.findall(r"(?:^|\n)(?:[\*\-\+]|\d+\.)\s+(.*)", list_content)

        if items:
            # Check if it's ordered (numbered) or unordered
            is_ordered = bool(re.match(r"(?:^|\n)\d+\.", list_content))
            lists.append(
                {
                    "type": "ordered" if is_ordered else "unordered",
                    "items": [item.strip() for item in items],
                }
            )

    return lists


def extract_tables(content: str) -> List[Dict[str, Any]]:
    """
    Extract tables from the markdown content.

    Args:
        content: Markdown content

    Returns:
        List of tables with headers and rows
    """
    tables = []
    # Find table regions (headers and separator line followed by rows)
    table_pattern = r"\|(.+?)\|\s*\n\|[-:| ]+\|\s*\n(\|.+\|\s*\n)+"

    for match in re.finditer(table_pattern, content, re.MULTILINE):
        table_content = match.group(0)
        lines = table_content.strip().split("\n")

        # Extract headers
        headers = [cell.strip() for cell in lines[0].split("|")[1:-1]]

        # Skip the separator line
        rows = []
        for line in lines[2:]:
            if "|" in line:
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
                rows.append(cells)

        tables.append({"headers": headers, "rows": rows})

    return tables


def extract_images(content: str) -> List[Dict[str, str]]:
    """
    Extract images from the markdown content.

    Args:
        content: Markdown content

    Returns:
        List of images with alt text and URLs
    """
    images = []
    image_pattern = r"!\[(.*?)\]\((.*?)\)"

    for match in re.finditer(image_pattern, content):
        alt_text = match.group(1).strip()
        url = match.group(2).strip()
        images.append({"alt_text": alt_text, "url": url})

    return images
