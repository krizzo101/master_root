# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Document Analyzer Module","description":"Module for analyzing documentation files and extracting structured information","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":22,"line_end":30},{"name":"DocumentAnalyzer Class","description":"Main class for document analysis","line_start":33,"line_end":152},{"name":"__init__ Method","description":"Constructor for DocumentAnalyzer class","line_start":47,"line_end":72},{"name":"analyze_document Method","description":"Main document analysis method","line_start":73,"line_end":126},{"name":"extract_key_concepts Method","description":"Method to extract key concepts from documents","line_start":127,"line_end":177},{"name":"detect_document_type Method","description":"Method to detect document type","line_start":178,"line_end":230}],"key_elements":[{"name":"DocumentAnalyzer","description":"Main document analysis class","line":33},{"name":"__init__","description":"Constructor method for DocumentAnalyzer","line":47},{"name":"analyze_document","description":"Document analysis method","line":73},{"name":"extract_key_concepts","description":"Method to extract key concepts from document content","line":127},{"name":"detect_document_type","description":"Method to detect document type based on file content","line":178}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Document Analyzer Module","description":"Module for analyzing documentation files and extracting structured information","last_updated":"2023-03-11","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":22,"line_end":30},
# {"name":"DocumentAnalyzer Class","description":"Main class for document analysis","line_start":33,"line_end":152},
# {"name":"analyze_document Method","description":"Main document analysis method","line_start":55,"line_end":94},
# {"name":"extract_key_concepts Method","description":"Method to extract key concepts from documents","line_start":96,"line_end":128},
# {"name":"detect_document_type Method","description":"Method to detect document type","line_start":130,"line_end":152}
# ],
# "key_elements":[
# {"name":"DocumentAnalyzer","description":"Main document analysis class","line":33},
# {"name":"analyze_document","description":"Document analysis method","line":55}
# ]
# }
# FILE_MAP_END

"""
Document Analyzer Module for Documentation Rule Generator.

This module analyzes documentation files and extracts structured information.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Any

from ..extractors.content_extractor import ContentExtractor
from ..mappers.source_mapper import SourceMapper
from ..mappers.cross_reference_detector import CrossReferenceDetector
from ..mappers.taxonomy_mapper import TaxonomyMapper
from ..inventory.document_inventory import DocumentInventory

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """
    Analyzes documentation files and extracts structured information.
    """

    def __init__(
        self,
        inventory: DocumentInventory,
        content_extractor: ContentExtractor = None,
        source_mapper: SourceMapper = None,
        cross_reference_detector: CrossReferenceDetector = None,
        taxonomy_mapper: TaxonomyMapper = None,
    ):
        """
        Initialize the document analyzer.

        Args:
            inventory: Document inventory instance
            content_extractor: Content extractor instance
            source_mapper: Source mapper instance
            cross_reference_detector: Cross reference detector instance
            taxonomy_mapper: Taxonomy mapper instance
        """
        self.inventory = inventory
        self.content_extractor = content_extractor or ContentExtractor()
        self.source_mapper = source_mapper or SourceMapper(inventory)
        self.cross_reference_detector = (
            cross_reference_detector or CrossReferenceDetector(inventory)
        )
        self.taxonomy_mapper = taxonomy_mapper

        logger.info("Initialized DocumentAnalyzer")

    def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a document and extract structured information.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Analyzing document: {file_path}")

        try:
            # Extract base content
            content = self.content_extractor.extract(file_path)

            if not content:
                logger.warning(f"Failed to extract content from {file_path}")
                return {}

            # Create analysis result
            result = {
                "file_path": file_path,
                "content": content,
                "document_type": self.detect_document_type(file_path, content),
                "timestamp": content.get("timestamp"),
                "concepts": self.extract_key_concepts(content),
            }

            # Add cross-references
            if self.cross_reference_detector:
                references = self.cross_reference_detector.detect_references(content)
                if references:
                    result["references"] = references

            # Map to source
            if self.source_mapper:
                source_mapping = self.source_mapper.map_content(content)
                if source_mapping:
                    result["source_mapping"] = source_mapping

            # Map to taxonomy categories
            if self.taxonomy_mapper:
                category_mapping = self.taxonomy_mapper.map_to_categories(content)
                if category_mapping:
                    result["category_mapping"] = category_mapping

            logger.info(f"Successfully analyzed document: {file_path}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing document {file_path}: {str(e)}")
            return {"file_path": file_path, "error": str(e)}

    def extract_key_concepts(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract key concepts from document content.

        Args:
            content: Document content

        Returns:
            List of key concepts
        """
        concepts = []

        if not content or "text" not in content:
            return concepts

        try:
            text = content["text"]

            # Extract markdown headers
            headers = re.findall(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE)
            for header_level, header_text in headers:
                concepts.append(
                    {
                        "term": header_text.strip(),
                        "type": "header",
                        "level": len(header_level),
                        "importance": 1.0,
                    }
                )

            # Extract code block languages
            code_blocks = re.findall(r"```(\w+)", text)
            for language in code_blocks:
                if language and language not in ["", "text"]:
                    concepts.append({"term": language, "type": "code_language"})

            # Extract emphasized terms
            emphasized = re.findall(r"\*\*([^*]+)\*\*", text)
            for term in emphasized:
                concepts.append({"term": term.strip(), "type": "emphasized"})

            return concepts

        except Exception as e:
            logger.error(f"Error extracting key concepts: {str(e)}")
            return concepts

    def detect_document_type(self, file_path: str, content: Dict[str, Any]) -> str:
        """
        Detect document type.

        Args:
            file_path: Path to the document file
            content: Document content

        Returns:
            Document type
        """
        # Default type
        doc_type = "unknown"

        try:
            # Check file extension
            extension = Path(file_path).suffix.lower()

            if extension == ".md":
                if "text" in content:
                    text = content["text"]

                    # Check for rule pattern
                    if re.search(r"^#+\s+.*rule", text, re.IGNORECASE | re.MULTILINE):
                        return "rule"

                    # Check for procedure pattern
                    if re.search(
                        r"^#+\s+.*procedure|step", text, re.IGNORECASE | re.MULTILINE
                    ):
                        return "procedure"

                    # Check for reference pattern
                    if re.search(
                        r"^#+\s+.*reference", text, re.IGNORECASE | re.MULTILINE
                    ):
                        return "reference"

                return "markdown"

            elif extension in [".txt"]:
                return "text"

            elif extension in [".json"]:
                return "json"

            elif extension in [".yaml", ".yml"]:
                return "yaml"

            elif extension in [".xml"]:
                return "xml"

            return doc_type

        except Exception as e:
            logger.error(f"Error detecting document type: {str(e)}")
            return doc_type
