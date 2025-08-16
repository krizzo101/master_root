# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Cross Reference Detector Module","description":"Module for detecting cross-references between documentation files","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":3,"line_end":28},{"name":"CrossReferenceDetector Class","description":"Main class for cross-reference detection","line_start":30,"line_end":100},{"name":"detect_references Method","description":"Main method to detect references","line_start":42,"line_end":100},{"name":"Helper Methods","description":"Private methods for processing references","line_start":104,"line_end":181}],"key_elements":[{"name":"CrossReferenceDetector","description":"Main cross-reference detection class","line":36},{"name":"__init__","description":"Constructor for CrossReferenceDetector class","line":41},{"name":"detect_references","description":"Reference detection method","line":51},{"name":"_process_markdown_links","description":"Processes markdown links in content","line":104},{"name":"_process_includes","description":"Processes include and import statements in content","line":129},{"name":"_process_direct_mentions","description":"Processes direct mentions of other documents","line":150}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Cross Reference Detector Module","description":"Module for detecting cross-references between documentation files","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":22,"line_end":28},
# {"name":"CrossReferenceDetector Class","description":"Main class for cross-reference detection","line_start":31,"line_end":100},
# {"name":"detect_references Method","description":"Main method to detect references","line_start":42,"line_end":100}
# ],
# "key_elements":[
# {"name":"CrossReferenceDetector","description":"Main cross-reference detection class","line":31},
# {"name":"detect_references","description":"Reference detection method","line":42}
# ]
# }
# FILE_MAP_END

"""
Cross Reference Detector Module for Documentation Rule Generator.

This module detects cross-references between documentation files.
"""

import os
import re
import logging
from typing import Dict, List, Any

from ..inventory.document_inventory import DocumentInventory

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CrossReferenceDetector:
    """
    Detects cross-references between documentation files.
    """

    def __init__(self, inventory: DocumentInventory = None):
        """
        Initialize the cross-reference detector.

        Args:
            inventory: Document inventory
        """
        self.inventory = inventory
        logger.info("Initialized CrossReferenceDetector")

    def detect_references(self, content: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Detect references to other documents.

        Args:
            content: Extracted content

        Returns:
            List of references
        """
        file_path = content.get("file_path", "unknown")
        logger.info(f"Detecting references in {file_path}")

        references = []

        try:
            # Get the text content, first from text field, then from content field if needed
            text_content = ""

            if "text" in content:
                text_content = content["text"]
            elif (
                "content" in content
                and isinstance(content["content"], dict)
                and "text" in content["content"]
            ):
                text_content = content["content"]["text"]
            elif "content" in content and isinstance(content["content"], str):
                text_content = content["content"]

            # Skip empty content
            if not text_content:
                logger.warning(f"Empty content for {file_path}")
                return references

            # Process markdown links [text](link)
            self._process_markdown_links(text_content, references)

            # Process includes and imports
            self._process_includes(text_content, references)

            # Process direct mentions
            title = ""
            if "title" in content:
                title = content["title"]
            elif (
                "content" in content
                and isinstance(content["content"], dict)
                and "title" in content["content"]
            ):
                title = content["content"]["title"]

            self._process_direct_mentions(text_content, title, references)

            logger.info(f"Detected {len(references)} references in {file_path}")
            return references

        except Exception as e:
            logger.error(f"Error detecting references: {str(e)}")
            return references

    def _process_markdown_links(self, content: str, references: List[Dict[str, str]]):
        """
        Process markdown links in content.

        Args:
            content: Document content
            references: List to add references to
        """
        # Match [text](link) pattern
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        matches = re.findall(link_pattern, content)

        for text, link in matches:
            # Skip external links and anchors
            if link.startswith(("http:", "https:", "ftp:", "mailto:", "#")):
                continue

            # Create reference
            references.append(
                {"text": text, "link": link, "type": "markdown_link", "target": link}
            )

    def _process_includes(self, content: str, references: List[Dict[str, str]]):
        """
        Process include and import statements in content.

        Args:
            content: Document content
            references: List to add references to
        """
        # Match include/import/require patterns
        include_pattern = r'(?:include|import|require)\s+[\'"]([^\'"]+)[\'"]'
        matches = re.findall(include_pattern, content)

        for path in matches:
            # Create reference
            references.append(
                {
                    "text": f"Import of {os.path.basename(path)}",
                    "link": path,
                    "type": "include",
                    "target": path,
                }
            )

    def _process_direct_mentions(
        self, content: str, title: str, references: List[Dict[str, str]]
    ):
        """
        Process direct mentions of other documents.

        Args:
            content: Document content
            title: Document title
            references: List to add references to
        """
        # Skip if no inventory
        if (
            not self.inventory
            or not hasattr(self.inventory, "documents")
            or not self.inventory.documents
        ):
            return

        # Check for mentions of other document titles
        for doc_id, doc_info in self.inventory.documents.items():
            doc_title = ""
            if "metadata" in doc_info and "title" in doc_info["metadata"]:
                doc_title = doc_info["metadata"]["title"]

            # Skip if same document or no title
            if not doc_title or doc_title == title:
                continue

            # Check for mentions
            if doc_title in content:
                # Create reference
                references.append(
                    {
                        "text": f"Mention of {doc_title}",
                        "link": doc_id,
                        "type": "mention",
                        "target": doc_id,
                    }
                )
