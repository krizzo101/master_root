# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Document Inventory Module","description":"Module for maintaining a document inventory","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":3,"line_end":6},{"name":"DocumentInventory Class","description":"Main class for document inventory","line_start":7,"line_end":143},{"name":"__init__ Method","description":"Constructor for initializing the document inventory","line_start":43,"line_end":49},{"name":"add_document Method","description":"Method to add a document to the inventory","line_start":53,"line_end":74},{"name":"get_document Method","description":"Method to get a document from the inventory","line_start":76,"line_end":90},{"name":"get_documents Method","description":"Method to get all documents from the inventory","line_start":92,"line_end":101},{"name":"get_document_count Method","description":"Method to get the count of documents in the inventory","line_start":103,"line_end":106},{"name":"get_documents_by_type Method","description":"Method to get documents by type","line_start":108,"line_end":128},{"name":"get_type_distribution Method","description":"Method to get distribution of document types","line_start":130,"line_end":143}],"key_elements":[{"name":"DocumentInventory","description":"Main document inventory class","line":38},{"name":"__init__","description":"Constructor method for DocumentInventory","line":43},{"name":"add_document","description":"Method to add a document","line":53},{"name":"get_document","description":"Method to retrieve a document","line":76},{"name":"get_documents","description":"Method to retrieve all documents","line":92},{"name":"get_document_count","description":"Method to count documents","line":103},{"name":"get_documents_by_type","description":"Method to retrieve documents by type","line":108},{"name":"get_type_distribution","description":"Method to retrieve document type distribution","line":130}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Document Inventory Module","description":"Module for maintaining a document inventory","last_updated":"2023-03-11","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":22,"line_end":27},
# {"name":"DocumentInventory Class","description":"Main class for document inventory","line_start":30,"line_end":143},
# {"name":"add_document Method","description":"Method to add a document to the inventory","line_start":48,"line_end":74},
# {"name":"get_document Method","description":"Method to get a document from the inventory","line_start":76,"line_end":90},
# {"name":"get_documents Method","description":"Method to get all documents from the inventory","line_start":92,"line_end":101},
# {"name":"get_document_count Method","description":"Method to get the count of documents in the inventory","line_start":103,"line_end":106},
# {"name":"get_document_by_type Method","description":"Method to get documents by type","line_start":108,"line_end":128},
# {"name":"get_type_distribution Method","description":"Method to get distribution of document types","line_start":130,"line_end":143}
# ],
# "key_elements":[
# {"name":"DocumentInventory","description":"Main document inventory class","line":30},
# {"name":"add_document","description":"Method to add a document","line":48}
# ]
# }
# FILE_MAP_END

"""
Document Inventory Module for Documentation Rule Generator.

This module maintains an inventory of documents and their metadata.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentInventory:
    """
    Maintains an inventory of documents and their metadata.
    """

    def __init__(self):
        """
        Initialize the document inventory.
        """
        # Initialize storage
        self.documents = {}
        self.document_types = {}

        logger.info("Initialized DocumentInventory")

    def add_document(
        self, file_path: str, doc_type: str = "unknown", metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a document to the inventory.

        Args:
            file_path: Path to the document file
            doc_type: Type of the document
            metadata: Document metadata

        Returns:
            True if the document was added successfully, False otherwise
        """
        try:
            # Convert to Path object and normalize
            path = Path(file_path)
            normalized_path = str(path.resolve())

            # Add to inventory
            self.documents[normalized_path] = {
                "file_path": normalized_path,
                "type": doc_type,
                "metadata": metadata or {},
                "added": True,
            }

            # Update document type mapping
            if doc_type not in self.document_types:
                self.document_types[doc_type] = set()

            self.document_types[doc_type].add(normalized_path)

            logger.debug(f"Added document to inventory: {normalized_path}")
            return True

        except Exception as e:
            logger.error(f"Error adding document to inventory: {str(e)}")
            return False

    def get_document(self, file_path: str) -> Dict[str, Any]:
        """
        Get a document from the inventory.

        Args:
            file_path: Path to the document file

        Returns:
            Document data if found, empty dict otherwise
        """
        try:
            # Convert to Path object and normalize
            path = Path(file_path)
            normalized_path = str(path.resolve())

            return self.documents.get(normalized_path, {})

        except Exception as e:
            logger.error(f"Error getting document from inventory: {str(e)}")
            return {}

    def get_documents(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all documents from the inventory.

        Returns:
            Dictionary of all documents
        """
        try:
            return self.documents

        except Exception as e:
            logger.error(f"Error getting documents from inventory: {str(e)}")
            return {}

    def get_document_count(self) -> int:
        """
        Get the count of documents in the inventory.

        Returns:
            Number of documents
        """
        return len(self.documents)

    def get_documents_by_type(self, doc_type: str) -> List[Dict[str, Any]]:
        """
        Get documents by type.

        Args:
            doc_type: Type of documents to get

        Returns:
            List of documents of the specified type
        """
        try:
            # Get document paths for the specified type
            doc_paths = self.document_types.get(doc_type, set())

            # Get document data for each path
            documents = []
            for path in doc_paths:
                doc_data = self.documents.get(path)
                if doc_data:
                    documents.append(doc_data)

            return documents

        except Exception as e:
            logger.error(f"Error getting documents by type: {str(e)}")
            return []

    def get_type_distribution(self) -> Dict[str, int]:
        """
        Get distribution of document types.

        Returns:
            Dictionary mapping document types to counts
        """
        try:
            distribution = {}

            for doc_type, doc_paths in self.document_types.items():
                distribution[doc_type] = len(doc_paths)

            return distribution

        except Exception as e:
            logger.error(f"Error getting type distribution: {str(e)}")
            return {}
