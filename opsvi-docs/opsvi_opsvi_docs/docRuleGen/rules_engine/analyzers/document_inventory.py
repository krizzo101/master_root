# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Document Inventory Module","description":"Module for maintaining inventory of documentation files and their relationships","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":22,"line_end":37},{"name":"DocumentInventory Class","description":"Main class for document inventory management","line_start":39,"line_end":127},{"name":"add_document Method","description":"Method to add document to inventory","line_start":45,"line_end":62},{"name":"build_relationships Method","description":"Method to build document relationships","line_start":84,"line_end":90},{"name":"get_inventory Method","description":"Method to get inventory data","line_start":119,"line_end":126},{"name":"get_type_distribution Method","description":"Method to get document type distribution","line_start":128,"line_end":138},{"name":"find_related_documents Method","description":"Method to find related documents","line_start":143,"line_end":155},{"name":"Private Methods","description":"Private utility methods for internal processing","line_start":158,"line_end":226}],"key_elements":[{"name":"DocumentInventory","description":"Main inventory management class","line":40},{"name":"__init__","description":"Constructor for DocumentInventory class","line":45},{"name":"add_document","description":"Document addition method","line":53},{"name":"build_relationships","description":"Relationship building method","line":84},{"name":"get_inventory","description":"Method to retrieve the document inventory","line":119},{"name":"get_type_distribution","description":"Method to get distribution of document types","line":128},{"name":"find_related_documents","description":"Method to find documents related to a specific document","line":143},{"name":"_is_text_file","description":"Check if a file is a text file based on extension","line":158},{"name":"_find_references","description":"Find references in document content","line":172},{"name":"_find_document_by_path","description":"Find a document in the inventory by its path","line":202}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Document Inventory Module","description":"Module for maintaining inventory of documentation files and their relationships","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":22,"line_end":27},
# {"name":"DocumentInventory Class","description":"Main class for document inventory management","line_start":30,"line_end":127},
# {"name":"add_document Method","description":"Method to add document to inventory","line_start":42,"line_end":62},
# {"name":"build_relationships Method","description":"Method to build document relationships","line_start":64,"line_end":90},
# {"name":"get_inventory Method","description":"Method to get inventory data","line_start":92,"line_end":99},
# {"name":"get_type_distribution Method","description":"Method to get document type distribution","line_start":101,"line_end":112},
# {"name":"find_related_documents Method","description":"Method to find related documents","line_start":114,"line_end":127}
# ],
# "key_elements":[
# {"name":"DocumentInventory","description":"Main inventory management class","line":30},
# {"name":"add_document","description":"Document addition method","line":42},
# {"name":"build_relationships","description":"Relationship building method","line":64}
# ]
# }
# FILE_MAP_END

"""
Document Inventory Module for Documentation Rule Generator.

This module provides functionality to maintain an inventory of documentation files
and their relationships.
"""

import os
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentInventory:
    """
    Maintains an inventory of documentation files and their relationships.
    """

    def __init__(self):
        """
        Initialize the document inventory.
        """
        self.documents = {}
        self.relationships = {}
        logger.info("Initialized DocumentInventory")

    def add_document(self, file_path: Path, doc_type: str, metadata: Dict[str, Any]):
        """
        Add a document to the inventory.

        Args:
            file_path: Path to the document
            doc_type: Type of document
            metadata: Document metadata
        """
        # Generate a unique ID for the document (normalized path)
        try:
            # Use relative path as ID if possible
            doc_id = str(file_path)

            self.documents[doc_id] = {
                "path": str(file_path),
                "type": doc_type,
                "metadata": metadata,
            }

            # Initialize relationships entry
            if doc_id not in self.relationships:
                self.relationships[doc_id] = {"references": [], "referenced_by": []}

            logger.debug(f"Added document {doc_id} to inventory")
        except Exception as e:
            logger.error(f"Error adding document to inventory: {str(e)}")

    def build_relationships(self):
        """
        Build relationships between documents based on references.
        """
        logger.info("Building document relationships")

        try:
            # Patterns to look for references
            # - Markdown links: [text](link)
            # - Import/include statements
            # - Direct mentions of other document names
            link_pattern = r"\[.*?\]\((.*?)\)"
            import_pattern = r'(?:import|include|require)\s+[\'"]([^\'"]+)[\'"]'

            # Process each document
            for doc_id, doc_info in self.documents.items():
                file_path = doc_info["path"]

                # Skip non-text files
                if not self._is_text_file(file_path):
                    continue

                # Read file content
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Find references
                    self._find_references(doc_id, content)

                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error building relationships: {str(e)}")

    def get_inventory(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the complete inventory.

        Returns:
            Dictionary containing all document information
        """
        return self.documents

    def get_type_distribution(self) -> Dict[str, int]:
        """
        Get distribution of document types.

        Returns:
            Dictionary mapping document types to counts
        """
        distribution = {}
        for doc in self.documents.values():
            doc_type = doc["type"]
            distribution[doc_type] = distribution.get(doc_type, 0) + 1

        logger.info(f"Document type distribution: {distribution}")
        return distribution

    def find_related_documents(self, doc_id: str) -> Dict[str, List[str]]:
        """
        Find documents related to the specified document.

        Args:
            doc_id: ID of the document

        Returns:
            Dictionary containing lists of references and referenced_by documents
        """
        if doc_id not in self.relationships:
            return {"references": [], "referenced_by": []}

        return self.relationships[doc_id]

    def _is_text_file(self, file_path: str) -> bool:
        """
        Check if a file is a text file based on extension.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is a text file, False otherwise
        """
        text_extensions = [
            ".md",
            ".txt",
            ".html",
            ".json",
            ".yml",
            ".yaml",
            ".py",
            ".js",
            ".ts",
            ".css",
        ]
        extension = Path(file_path).suffix.lower()
        return extension in text_extensions

    def _find_references(self, doc_id: str, content: str):
        """
        Find references in document content.

        Args:
            doc_id: ID of the document
            content: Document content
        """
        # Look for markdown links
        link_pattern = r"\[.*?\]\((.*?)\)"
        links = re.findall(link_pattern, content)

        # Process each link
        for link in links:
            # Skip external links and anchors
            if link.startswith(("http:", "https:", "ftp:", "mailto:", "#")):
                continue

            # Find document by path or name
            target_doc_id = self._find_document_by_path(link)
            if target_doc_id:
                # Add to relationships
                if target_doc_id != doc_id:  # Avoid self-references
                    if target_doc_id not in self.relationships[doc_id]["references"]:
                        self.relationships[doc_id]["references"].append(target_doc_id)

                    # Add reverse relationship
                    if doc_id not in self.relationships[target_doc_id]["referenced_by"]:
                        self.relationships[target_doc_id]["referenced_by"].append(
                            doc_id
                        )

    def _find_document_by_path(self, path: str) -> str:
        """
        Find a document in the inventory by its path.

        Args:
            path: Path to look for

        Returns:
            Document ID if found, None otherwise
        """
        # Normalize path
        norm_path = os.path.normpath(path)

        # Check for exact match
        for doc_id, doc_info in self.documents.items():
            if norm_path in doc_info["path"]:
                return doc_id

        # Check for filename match
        filename = os.path.basename(norm_path)
        for doc_id, doc_info in self.documents.items():
            if filename == os.path.basename(doc_info["path"]):
                return doc_id

        return None
