# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"LLM Taxonomy Generator Module","description":"This module provides functionality for using LLM to generate taxonomies from document content, extracting concepts, hierarchies, and relationships through AI-powered analysis.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary libraries and modules for the functionality of the LLM Taxonomy Generator.","line_start":3,"line_end":14},{"name":"LLMTaxonomyGenerator Class","description":"Class definition for LLMTaxonomyGenerator, which encapsulates methods for generating and managing taxonomies.","line_start":16,"line_end":145}],"key_elements":[{"name":"LLMTaxonomyGenerator","description":"Class for generating document taxonomies using Large Language Models.","line":17},{"name":"__init__","description":"Constructor for initializing the LLM Taxonomy Generator.","line":25},{"name":"generate_taxonomy","description":"Method to generate a taxonomy from a document using LLM.","line":34},{"name":"extract_key_concepts","description":"Method to extract key concepts from document content.","line":75},{"name":"merge_taxonomies","description":"Method to merge multiple taxonomies into a unified taxonomy.","line":99},{"name":"logger","description":"Logger instance for logging information and errors.","line":14}]}
"""
# FILE_MAP_END

"""
LLM Taxonomy Generator Module.

This module provides functionality for using LLM to generate taxonomies from document content,
extracting concepts, hierarchies, and relationships through AI-powered analysis.
"""

import logging
from typing import Dict, Any, List

from ..connectors.llm_orchestrator import LLMOrchestrator
from .content_extractor import ContentExtractor

logger = logging.getLogger(__name__)


class LLMTaxonomyGenerator:
    """
    Generate document taxonomies using Large Language Models.

    This class utilizes LLMs to extract and organize document concepts into a
    structured taxonomy, identifying hierarchies, relationships, and key components.
    """

    def __init__(self):
        """
        Initialize the LLM taxonomy generator.
        """
        self.orchestrator = LLMOrchestrator()
        self.content_extractor = ContentExtractor()

        logger.info("Initialized LLM taxonomy generator")

    def generate_taxonomy(self, document_path: str) -> Dict[str, Any]:
        """
        Generate a taxonomy from a document using LLM.

        Args:
            document_path: Path to the document file

        Returns:
            Taxonomy dictionary with concepts, hierarchies, and relationships
        """
        logger.info(f"Generating taxonomy for document: {document_path}")

        try:
            # Extract document content
            document_content = self.content_extractor.extract(document_path)
            if not document_content or "error" in document_content:
                error_msg = (
                    document_content.get("error", "Unknown error in content extraction")
                    if isinstance(document_content, dict)
                    else "Failed to extract document content"
                )
                logger.error(f"Content extraction failed: {error_msg}")
                return {"error": error_msg}

            # Generate taxonomy using LLM
            taxonomy = self.orchestrator.generate_taxonomy(document_content)
            if not taxonomy or "error" in taxonomy:
                error_msg = (
                    taxonomy.get("error", "Unknown error in taxonomy generation")
                    if isinstance(taxonomy, dict)
                    else "Failed to generate taxonomy"
                )
                logger.error(f"Taxonomy generation failed: {error_msg}")
                return {"error": error_msg}

            # Add taxonomy metadata
            taxonomy["document_path"] = document_path
            if "title" in document_content:
                taxonomy["document_title"] = document_content["title"]
            if "file_path" in document_content:
                taxonomy["source_file"] = document_content["file_path"]

            logger.info(
                f"Successfully generated taxonomy with {len(taxonomy.get('concepts', []))} concepts"
            )
            return taxonomy

        except Exception as e:
            logger.error(f"Error generating taxonomy: {str(e)}")
            return {"error": f"Error generating taxonomy: {str(e)}"}

    def extract_key_concepts(
        self, document_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract key concepts from document content.

        Args:
            document_content: Extracted document content

        Returns:
            List of key concepts with metadata
        """
        try:
            # Use the orchestrator to extract concepts
            taxonomy = self.orchestrator.generate_taxonomy(document_content)

            # Return the concepts section
            if (
                taxonomy
                and "concepts" in taxonomy
                and isinstance(taxonomy["concepts"], list)
            ):
                return taxonomy["concepts"]

            return []

        except Exception as e:
            logger.error(f"Error extracting key concepts: {str(e)}")
            return []

    def merge_taxonomies(self, taxonomies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple taxonomies into a unified taxonomy.

        Args:
            taxonomies: List of taxonomy dictionaries

        Returns:
            Merged taxonomy dictionary
        """
        if not taxonomies:
            return {}

        merged = {"concepts": [], "hierarchies": [], "relationships": [], "sources": []}

        # Track concepts to avoid duplication
        concept_ids = set()

        # Process each taxonomy
        for taxonomy in taxonomies:
            # Skip invalid taxonomies
            if not isinstance(taxonomy, dict):
                continue

            # Add source
            source = {
                "document_path": taxonomy.get("document_path", "unknown"),
                "document_title": taxonomy.get("document_title", "Untitled"),
            }
            merged["sources"].append(source)

            # Add concepts
            for concept in taxonomy.get("concepts", []):
                concept_id = concept.get("id")
                if concept_id and concept_id not in concept_ids:
                    concept_ids.add(concept_id)
                    merged["concepts"].append(concept)

            # Add hierarchies and relationships
            for key in ["hierarchies", "relationships"]:
                merged[key].extend(taxonomy.get(key, []))

        return merged
