# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Document Analysis Workflow Module","description":"Module for orchestrating the document analysis process","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":22,"line_end":30},{"name":"DocumentAnalysisWorkflow Class","description":"Main class for document analysis workflow","line_start":33,"line_end":136},{"name":"__init__ Method","description":"Constructor for initializing the document analysis workflow","line_start":48,"line_end":90},{"name":"run Method","description":"Main workflow execution method","line_start":91,"line_end":128},{"name":"analyze_document Method","description":"Method to analyze a single document","line_start":129,"line_end":155},{"name":"analyze_directory Method","description":"Method to analyze all documents in a directory","line_start":156,"line_end":185},{"name":"scan_documents Method","description":"Method to scan for documentation files","line_start":186,"line_end":198},{"name":"load_taxonomy Method","description":"Method to load taxonomy from file","line_start":199,"line_end":229}],"key_elements":[{"name":"DocumentAnalysisWorkflow","description":"Main workflow orchestration class","line":33},{"name":"__init__","description":"Constructor for initializing the document analysis workflow","line":48},{"name":"run","description":"Main workflow execution method","line":91},{"name":"analyze_document","description":"Method to analyze a single document","line":128},{"name":"analyze_directory","description":"Method to analyze all documents in a directory","line":155},{"name":"scan_documents","description":"Method to scan for documentation files","line":186},{"name":"load_taxonomy","description":"Method to load taxonomy from file","line":199}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Document Analysis Workflow Module","description":"Module for orchestrating the document analysis process","last_updated":"2023-03-11","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":22,"line_end":30},
# {"name":"DocumentAnalysisWorkflow Class","description":"Main class for document analysis workflow","line_start":33,"line_end":136},
# {"name":"run Method","description":"Main workflow execution method","line_start":58,"line_end":89},
# {"name":"analyze_document Method","description":"Method to analyze a single document","line_start":91,"line_end":109},
# {"name":"analyze_directory Method","description":"Method to analyze all documents in a directory","line_start":111,"line_end":136}
# ],
# "key_elements":[
# {"name":"DocumentAnalysisWorkflow","description":"Main workflow orchestration class","line":33},
# {"name":"run","description":"Main workflow execution method","line":58}
# ]
# }
# FILE_MAP_END

"""
Document Analysis Workflow Module for Documentation Rule Generator.

This module orchestrates the document analysis process.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..analyzers.document_analyzer import DocumentAnalyzer
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


class DocumentAnalysisWorkflow:
    """
    Orchestrates the document analysis process.
    """

    def __init__(
        self,
        doc_dir: str,
        taxonomy_file: Optional[str] = None,
        output_dir: Optional[str] = None,
        max_workers: int = 4,
        file_extensions: List[str] = None,
    ):
        """
        Initialize the document analysis workflow.

        Args:
            doc_dir: Directory containing documentation files
            taxonomy_file: Path to taxonomy file (optional)
            output_dir: Directory to save output (optional)
            max_workers: Maximum number of worker threads
            file_extensions: List of file extensions to process
        """
        self.doc_dir = Path(doc_dir)
        self.taxonomy_file = taxonomy_file
        self.output_dir = (
            Path(output_dir) if output_dir else Path(doc_dir) / "analysis_output"
        )
        self.max_workers = max_workers
        self.file_extensions = file_extensions or [
            ".md",
            ".txt",
            ".yaml",
            ".yml",
            ".json",
        ]

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.inventory = DocumentInventory()
        self.content_extractor = ContentExtractor()
        self.taxonomy_mapper = (
            TaxonomyMapper(self.load_taxonomy()) if taxonomy_file else None
        )
        self.source_mapper = SourceMapper(self.inventory)
        self.cross_reference_detector = CrossReferenceDetector(self.inventory)
        self.document_analyzer = DocumentAnalyzer(
            self.inventory,
            self.content_extractor,
            self.source_mapper,
            self.cross_reference_detector,
            self.taxonomy_mapper,
        )

        logger.info(
            f"Initialized DocumentAnalysisWorkflow for directory: {self.doc_dir}"
        )

    def run(self) -> Dict[str, Any]:
        """
        Run the document analysis workflow.

        Returns:
            Dictionary containing analysis results
        """
        logger.info("Starting document analysis workflow")

        try:
            # Scan for documentation files
            files = self.scan_documents()
            logger.info(f"Found {len(files)} documentation files to analyze")

            # Analyze all files
            results = self.analyze_directory(files)

            # Generate analysis summary
            summary = {
                "total_documents": len(files),
                "analyzed_documents": len(results),
                "documents_by_type": {},
                "status": "success",
            }

            # Count document types
            for file_result in results.values():
                doc_type = file_result.get("document_type", "unknown")
                summary["documents_by_type"][doc_type] = (
                    summary["documents_by_type"].get(doc_type, 0) + 1
                )

            logger.info("Document analysis workflow completed successfully")
            return summary

        except Exception as e:
            logger.error(f"Error in document analysis workflow: {str(e)}")
            return {"status": "error", "error": str(e)}

    def analyze_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a single document.

        Args:
            file_path: Path to the document

        Returns:
            Dictionary containing analysis result
        """
        try:
            # Analyze document
            result = self.document_analyzer.analyze_document(str(file_path))

            # Save result to output file
            if result:
                output_file = self.output_dir / f"{file_path.stem}_analysis.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    import json

                    json.dump(result, f, indent=2)

            return result

        except Exception as e:
            logger.error(f"Error analyzing document {file_path}: {str(e)}")
            return {"file_path": str(file_path), "error": str(e), "status": "error"}

    def analyze_directory(self, files: List[Path]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze all documents in a directory.

        Args:
            files: List of file paths to analyze

        Returns:
            Dictionary mapping file paths to analysis results
        """
        results = {}

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.analyze_document, file_path): file_path
                for file_path in files
            }

            # Process results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results[str(file_path)] = result
                    logger.info(f"Completed analysis of {file_path}")
                except Exception as e:
                    logger.error(f"Error analyzing {file_path}: {str(e)}")
                    results[str(file_path)] = {
                        "file_path": str(file_path),
                        "error": str(e),
                        "status": "error",
                    }

        return results

    def scan_documents(self) -> List[Path]:
        """
        Scan for documentation files in the specified directory.

        Returns:
            List of file paths
        """
        files = []

        for ext in self.file_extensions:
            files.extend(list(self.doc_dir.glob(f"**/*{ext}")))

        return files

    def load_taxonomy(self) -> Dict[str, Any]:
        """
        Load taxonomy from file.

        Returns:
            Dictionary containing taxonomy
        """
        try:
            if not self.taxonomy_file:
                return {}

            taxonomy_path = Path(self.taxonomy_file)

            if not taxonomy_path.exists():
                logger.warning(f"Taxonomy file not found: {taxonomy_path}")
                return {}

            with open(taxonomy_path, "r", encoding="utf-8") as f:
                if taxonomy_path.suffix.lower() in [".yaml", ".yml"]:
                    import yaml

                    return yaml.safe_load(f)
                elif taxonomy_path.suffix.lower() == ".json":
                    import json

                    return json.load(f)
                else:
                    logger.warning(f"Unsupported taxonomy file format: {taxonomy_path}")
                    return {}

        except Exception as e:
            logger.error(f"Error loading taxonomy file: {str(e)}")
            return {}
