"""Markdown parser module.

This module provides functionality for parsing Markdown content into document elements.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set

from markdown_it import MarkdownIt
from markdown_it.token import Token

from proj_mapper.models.code import Location
from proj_mapper.models.documentation import DocumentationElement, DocumentationType

# Configure logging
logger = logging.getLogger(__name__)

class MarkdownParser:
    """Parser for Markdown content.
    
    This class handles the parsing of Markdown content into structured document elements.
    """
    
    def __init__(self):
        """Initialize the Markdown parser."""
        self.parser = MarkdownIt()
        self.id_counter = 0
    
    def get_next_id(self) -> str:
        """Get the next unique ID.
        
        Returns:
            A unique ID string
        """
        self.id_counter += 1
        return f"md_{self.id_counter}"
    
    def extract_front_matter(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Extract front matter metadata from Markdown content.
        
        Args:
            content: The markdown content
            
        Returns:
            Tuple of (content without front matter, extracted metadata)
        """
        metadata: Dict[str, Any] = {}
        
        # Check for YAML front matter (---key: value---)
        yaml_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        yaml_match = re.search(yaml_pattern, content, re.DOTALL)
        if yaml_match:
            try:
                import yaml
                front_matter = yaml_match.group(1)
                metadata = yaml.safe_load(front_matter)
                content = content[yaml_match.end():]
            except (ImportError, yaml.YAMLError) as e:
                logger.warning(f"Failed to parse YAML front matter: {e}")
        
        # Check for JSON front matter (---{json}---)
        json_pattern = r"^---\s*\n(\{.*?\})\n---\s*\n"
        json_match = re.search(json_pattern, content, re.DOTALL)
        if json_match and not metadata:
            try:
                import json
                front_matter = json_match.group(1)
                metadata = json.loads(front_matter)
                content = content[json_match.end():]
            except (ImportError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to parse JSON front matter: {e}")
        
        return content, metadata
    
    def parse(self, content: str, file_path: str) -> List[DocumentationElement]:
        """Parse Markdown content and create documentation elements.
        
        Args:
            content: The Markdown content to parse
            file_path: Path to the file being analyzed
            
        Returns:
            List of documentation elements
        """
        # Reset ID counter
        self.id_counter = 0
        
        # Parse the Markdown content
        tokens = self.parser.parse(content)
        
        # Process tokens
        elements = self._process_tokens(tokens, file_path)
        
        return elements
    
    def _process_tokens(self, tokens: List[Token], file_path: str) -> List[DocumentationElement]:
        """Process Markdown tokens and create documentation elements.
        
        Args:
            tokens: List of parsed Markdown tokens
            file_path: Path to the file being analyzed
            
        Returns:
            List of documentation elements
        """
        elements: List[DocumentationElement] = []
        heading_stack: List[str] = []  # Stack to track parent headings
        current_section_id: Optional[str] = None
        line_offset = 1  # 1-indexed line numbers
        
        # First pass to extract headings and sections
        for i, token in enumerate(tokens):
            if token.type == 'heading_open':
                # Get heading level and content
                level = int(token.tag[1])  # 'h1' -> 1, 'h2' -> 2, etc.
                content_token = tokens[i + 1] if i + 1 < len(tokens) else None
                if not content_token or content_token.type != 'inline':
                    continue
                
                heading_text = content_token.content
                
                # Create section element
                section_id = self.get_next_id()
                location = Location(
                    file_path=file_path,
                    start_line=token.map[0] + line_offset if token.map else 0,
                    end_line=tokens[i + 2].map[1] + line_offset if tokens[i + 2].map else 0
                )
                
                # Determine parent based on heading level
                parent_id = None
                while heading_stack and len(heading_stack) >= level:
                    heading_stack.pop()
                if heading_stack:
                    parent_id = heading_stack[-1]
                
                # Create element
                section_element = DocumentationElement(
                    title=heading_text,
                    element_type=DocumentationType.SECTION,
                    location=location,
                    parent=parent_id,
                    content=heading_text,
                    metadata={"level": level}
                )
                elements.append(section_element)
                
                # Update parent-child relationships
                if parent_id:
                    for elem in elements:
                        if elem.title == parent_id:
                            elem.add_child(section_id)
                
                heading_stack.append(section_id)
                current_section_id = section_id
        
        # Second pass to extract content elements
        current_section_id = None
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Handle headings (to track current section)
            if token.type == 'heading_open':
                level = int(token.tag[1])
                content_token = tokens[i + 1] if i + 1 < len(tokens) else None
                if not content_token or content_token.type != 'inline':
                    i += 1
                    continue
                
                heading_text = content_token.content
                
                # Find the corresponding section ID
                for elem in elements:
                    if (elem.element_type == DocumentationType.SECTION and 
                        elem.title == heading_text and
                        elem.metadata.get("level") == level):
                        current_section_id = elem.title
                        break
                
                i += 3  # Skip heading_open, inline, heading_close
                continue
            
            # Handle paragraphs
            elif token.type == 'paragraph_open':
                content_token = tokens[i + 1] if i + 1 < len(tokens) else None
                if not content_token or content_token.type != 'inline':
                    i += 1
                    continue
                
                content = content_token.content
                location = Location(
                    file_path=file_path,
                    start_line=token.map[0] + line_offset if token.map else 0,
                    end_line=tokens[i + 2].map[1] + line_offset if tokens[i + 2].map else 0
                )
                
                para_id = self.get_next_id()
                para_element = DocumentationElement(
                    title=para_id,
                    element_type=DocumentationType.PARAGRAPH,
                    location=location,
                    parent=current_section_id,
                    content=content
                )
                elements.append(para_element)
                
                # Add to parent section
                if current_section_id:
                    for elem in elements:
                        if elem.title == current_section_id:
                            elem.add_child(para_id)
                
                i += 3  # Skip paragraph_open, inline, paragraph_close
                continue
            
            # Handle code blocks
            elif token.type == 'fence':
                lang = token.info.strip() if token.info else ''
                content = token.content
                location = Location(
                    file_path=file_path,
                    start_line=token.map[0] + line_offset if token.map else 0,
                    end_line=token.map[1] + line_offset if token.map else 0
                )
                
                code_id = self.get_next_id()
                code_element = DocumentationElement(
                    title=code_id,
                    element_type=DocumentationType.CODE_BLOCK,
                    location=location,
                    parent=current_section_id,
                    content=content,
                    metadata={"language": lang}
                )
                elements.append(code_element)
                
                # Add to parent section
                if current_section_id:
                    for elem in elements:
                        if elem.title == current_section_id:
                            elem.add_child(code_id)
                
                i += 1
                continue
            
            # Handle lists
            elif token.type == 'bullet_list_open' or token.type == 'ordered_list_open':
                list_type = "bullet" if token.type == 'bullet_list_open' else "ordered"
                start_idx = i
                nesting = 1
                j = i + 1
                
                # Find the end of the list
                while j < len(tokens) and nesting > 0:
                    if tokens[j].type == 'bullet_list_open' or tokens[j].type == 'ordered_list_open':
                        nesting += 1
                    elif tokens[j].type == 'bullet_list_close' or tokens[j].type == 'ordered_list_close':
                        nesting -= 1
                    j += 1
                
                end_idx = j - 1
                
                location = Location(
                    file_path=file_path,
                    start_line=token.map[0] + line_offset if token.map else 0,
                    end_line=tokens[end_idx].map[1] + line_offset if tokens[end_idx].map else 0
                )
                
                list_id = self.get_next_id()
                list_element = DocumentationElement(
                    title=list_id,
                    element_type=DocumentationType.LIST,
                    location=location,
                    parent=current_section_id,
                    content="",  # Combined content will be processed separately
                    metadata={"list_type": list_type}
                )
                elements.append(list_element)
                
                # Process list items (simplified)
                for k in range(start_idx + 1, end_idx):
                    if tokens[k].type == 'list_item_open':
                        item_start = k
                        item_nesting = 1
                        l = k + 1
                        
                        # Find the end of the list item
                        while l < end_idx and item_nesting > 0:
                            if tokens[l].type == 'list_item_open':
                                item_nesting += 1
                            elif tokens[l].type == 'list_item_close':
                                item_nesting -= 1
                            l += 1
                        
                        item_end = l - 1
                        
                        # Extract item content (simplified)
                        item_content = []
                        for m in range(item_start + 1, item_end):
                            if tokens[m].type == 'inline':
                                item_content.append(tokens[m].content)
                        
                        item_text = " ".join(item_content)
                        if item_text:
                            item_location = Location(
                                file_path=file_path,
                                start_line=tokens[item_start].map[0] + line_offset if tokens[item_start].map else 0,
                                end_line=tokens[item_end].map[1] + line_offset if tokens[item_end].map else 0
                            )
                            
                            item_id = self.get_next_id()
                            item_element = DocumentationElement(
                                title=item_id,
                                element_type=DocumentationType.LIST_ITEM,
                                location=item_location,
                                parent=list_id,
                                content=item_text
                            )
                            elements.append(item_element)
                            list_element.add_child(item_id)
                
                # Add list to parent section
                if current_section_id:
                    for elem in elements:
                        if elem.title == current_section_id:
                            elem.add_child(list_id)
                
                i = end_idx + 1
                continue
            
            # Handle other token types
            i += 1
        
        return elements 