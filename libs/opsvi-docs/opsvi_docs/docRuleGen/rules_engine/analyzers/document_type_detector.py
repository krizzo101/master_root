# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Document Type Detector Module","description":"Module for detecting document types and extracting metadata from documentation files","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":22,"line_end":33},{"name":"DocumentTypeDetector Class","description":"Main class for document type detection","line_start":34,"line_end":142},{"name":"__init__ Method","description":"Constructor for initializing the document type detector","line_start":45,"line_end":59},{"name":"detect_type Method","description":"Method to detect document type","line_start":60,"line_end":112},{"name":"extract_metadata Method","description":"Method to extract document metadata","line_start":113,"line_end":142}],"key_elements":[{"name":"DocumentTypeDetector","description":"Main class for document type detection","line":34},{"name":"__init__","description":"Constructor for initializing the document type detector","line":45},{"name":"detect_type","description":"Document type detection method","line":60},{"name":"extract_metadata","description":"Metadata extraction method","line":113}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Document Type Detector Module","description":"Module for detecting document types and extracting metadata from documentation files","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":22,"line_end":30},
# {"name":"DocumentTypeDetector Class","description":"Main class for document type detection","line_start":33,"line_end":142},
# {"name":"detect_type Method","description":"Method to detect document type","line_start":43,"line_end":85},
# {"name":"extract_metadata Method","description":"Method to extract document metadata","line_start":87,"line_end":142}
# ],
# "key_elements":[
# {"name":"DocumentTypeDetector","description":"Main class for document type detection","line":33},
# {"name":"detect_type","description":"Document type detection method","line":43},
# {"name":"extract_metadata","description":"Metadata extraction method","line":87}
# ]
# }
# FILE_MAP_END

"""
Document Type Detector Module for Documentation Rule Generator.

This module provides functionality to detect document types and extract metadata
from documentation files.
"""

import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentTypeDetector:
    """
    Detects the type of documentation file and extracts metadata.
    """

    def __init__(self):
        """
        Initialize the document type detector.
        """
        self.type_patterns = {
            "readme": r"readme\.md$",
            "api": r"api|endpoint|service|rest",
            "guide": r"guide|tutorial|how-to|howto",
            "reference": r"reference|specification|spec",
            "architecture": r"architecture|design|system",
            "code": r"code|implementation|library|module",
            "standard": r"standard|guideline|best.?practice|convention",
            "config": r"config|configuration|setting",
        }

    def detect_type(self, file_path: Path) -> str:
        """
        Detect the type of documentation file based on path and content.

        Args:
            file_path: Path to the file

        Returns:
            String indicating document type
        """
        logger.debug(f"Detecting type for {file_path}")

        # Default type
        doc_type = "general"

        try:
            # First check by filename and path
            file_name = file_path.name.lower()
            file_path_str = str(file_path).lower()

            # Check for readme files
            if re.search(r"readme\.md$", file_name, re.IGNORECASE):
                return "readme"

            # Check other types by path
            for type_name, pattern in self.type_patterns.items():
                if re.search(pattern, file_path_str, re.IGNORECASE):
                    return type_name

            # If type still not determined, check content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(4096)  # Read first 4KB

                # Check content for type indicators
                for type_name, pattern in self.type_patterns.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        return type_name

            # Determine by file extension
            extension = file_path.suffix.lower()
            if extension == ".md":
                return "markdown"
            elif extension == ".txt":
                return "text"
            elif extension == ".html":
                return "html"

            return doc_type

        except Exception as e:
            logger.error(f"Error detecting type for {file_path}: {str(e)}")
            return "unknown"

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a documentation file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing metadata
        """
        logger.debug(f"Extracting metadata for {file_path}")

        metadata = {
            "title": file_path.stem,
            "file_name": file_path.name,
            "file_path": str(file_path),
            "extension": file_path.suffix,
            "size_bytes": file_path.stat().st_size,
            "last_modified": datetime.fromtimestamp(
                file_path.stat().st_mtime
            ).isoformat(),
            "created": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
        }

        try:
            # Extract more metadata based on file type
            extension = file_path.suffix.lower()

            if extension == ".md":
                # For markdown files, try to extract title from first heading
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read(8192)  # Read first 8KB

                    # Look for frontmatter
                    frontmatter = {}
                    fm_match = re.search(r"^---\s*\n([\s\S]*?)\n---", content)
                    if fm_match:
                        try:
                            frontmatter = yaml.safe_load(fm_match.group(1))
                            if isinstance(frontmatter, dict):
                                metadata.update(
                                    {
                                        "frontmatter": frontmatter,
                                        "has_frontmatter": True,
                                    }
                                )
                                if "title" in frontmatter:
                                    metadata["title"] = frontmatter["title"]
                        except Exception as e:
                            logger.warning(f"Error parsing frontmatter: {str(e)}")

                    # Look for title in first heading if not in frontmatter
                    if metadata["title"] == file_path.stem:
                        heading_match = re.search(r"^#\s+(.*?)$", content, re.MULTILINE)
                        if heading_match:
                            metadata["title"] = heading_match.group(1).strip()

                    # Count headings and code blocks
                    metadata["headings_count"] = len(
                        re.findall(r"^#{1,6}\s+", content, re.MULTILINE)
                    )
                    metadata["code_blocks_count"] = len(re.findall(r"```", content))

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata for {file_path}: {str(e)}")
            return metadata
