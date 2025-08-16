# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Source Mapper Module","description":"Module for mapping content to rule categories and establishing source traceability","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":22,"line_end":32},{"name":"SourceMapper Class","description":"Main class for source mapping","line_start":33,"line_end":106},{"name":"map_content Method","description":"Main method to map content to categories","line_start":90,"line_end":138}],"key_elements":[{"name":"SourceMapper","description":"Main source mapping class","line":33},{"name":"__init__","description":"Constructor for SourceMapper class","line":44},{"name":"_load_taxonomy","description":"Method to load a taxonomy file","line":62},{"name":"map_content","description":"Content mapping method","line":89}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Source Mapper Module","description":"Module for mapping content to rule categories and establishing source traceability","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":22,"line_end":30},
# {"name":"SourceMapper Class","description":"Main class for source mapping","line_start":33,"line_end":106},
# {"name":"map_content Method","description":"Main method to map content to categories","line_start":70,"line_end":106}
# ],
# "key_elements":[
# {"name":"SourceMapper","description":"Main source mapping class","line":33},
# {"name":"map_content","description":"Content mapping method","line":70}
# ]
# }
# FILE_MAP_END

"""
Source Mapper Module for Documentation Rule Generator.

This module maps content to potential rule categories and establishes source traceability.
"""

import os
import logging
import yaml
from typing import Dict, Any

from ..inventory.document_inventory import DocumentInventory
from .cross_reference_detector import CrossReferenceDetector
from .taxonomy_mapper import TaxonomyMapper

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SourceMapper:
    """
    Maps content to potential rule categories and establishes source traceability.
    """

    def __init__(self, inventory: DocumentInventory = None, taxonomy_file: str = None):
        """
        Initialize the source mapper.

        Args:
            inventory: Document inventory
            taxonomy_file: Path to taxonomy file (optional)
        """
        self.inventory = inventory
        self.taxonomy = self._load_taxonomy(taxonomy_file) if taxonomy_file else None

        # Initialize components
        self.cross_ref_detector = CrossReferenceDetector(inventory)
        self.taxonomy_mapper = TaxonomyMapper(self.taxonomy)

        logger.info("Initialized SourceMapper")
        logger.debug(f"Taxonomy loaded: {bool(self.taxonomy)}")

    def _load_taxonomy(self, taxonomy_file: str) -> Dict[str, Any]:
        """
        Load a taxonomy file.

        Args:
            taxonomy_file: Path to the taxonomy file

        Returns:
            Loaded taxonomy
        """
        try:
            logger.info(f"Loading taxonomy from {taxonomy_file}")

            if not taxonomy_file or not os.path.exists(taxonomy_file):
                logger.warning(f"Taxonomy file not found: {taxonomy_file}")
                return None

            with open(taxonomy_file, "r", encoding="utf-8") as f:
                taxonomy = yaml.safe_load(f)

            logger.info(f"Loaded taxonomy: {taxonomy.get('taxonomy_name', 'Unnamed')}")
            return taxonomy

        except Exception as e:
            logger.error(f"Error loading taxonomy file: {str(e)}")
            return None

    def map_content(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map extracted content to potential rule categories.

        Args:
            extracted_content: Extracted content

        Returns:
            Mapping results
        """
        file_path = extracted_content.get("file_path", "unknown")
        logger.info(f"Mapping content from {file_path}")

        try:
            # Detect cross-references
            cross_refs = self.cross_ref_detector.detect_references(extracted_content)
            logger.debug(f"Detected {len(cross_refs)} cross-references")

            # Map to taxonomy categories
            category_mapping = self.taxonomy_mapper.map_to_categories(extracted_content)
            num_categories = (
                len(category_mapping) if isinstance(category_mapping, dict) else 0
            )
            logger.debug(f"Mapped content to {num_categories} categories")

            # Create simple traceability information
            traceability = {
                "source_file": file_path,
                "referenced_by": [],
                "references_to": [
                    ref.get("target", "") for ref in cross_refs if "target" in ref
                ],
                "categories": list(category_mapping.keys())
                if isinstance(category_mapping, dict)
                else [],
            }

            # Create mapping result
            result = {
                "content_id": file_path,
                "cross_references": cross_refs,
                "category_mapping": category_mapping,
                "traceability": traceability,
                "status": "success",
            }

            logger.info(f"Successfully mapped content from {file_path}")
            return result

        except Exception as e:
            logger.error(f"Error mapping content: {str(e)}")
            return {"content_id": file_path, "status": "error", "error": str(e)}
