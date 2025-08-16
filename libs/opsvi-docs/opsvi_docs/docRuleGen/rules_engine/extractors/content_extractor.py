# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Content Extractor Module","description":"Module for extracting content from various document types","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":3,"line_end":10},{"name":"ContentExtractor Class","description":"Main class for content extraction","line_start":11,"line_end":165},{"name":"extract Method","description":"Main extraction method","line_start":42,"line_end":68},{"name":"_extract_markdown Method","description":"Method to extract from markdown files","line_start":70,"line_end":96},{"name":"_extract_yaml Method","description":"Method to extract from YAML files","line_start":98,"line_end":119},{"name":"_extract_json Method","description":"Method to extract from JSON files","line_start":121,"line_end":142},{"name":"_extract_text Method","description":"Method to extract from text files","line_start":144,"line_end":165}],"key_elements":[{"name":"ContentExtractor","description":"Main content extraction class","line":11},{"name":"extract","description":"Main extraction method","line":42},{"name":"__init__","description":"Initializer for ContentExtractor class","line":45},{"name":"_extract_markdown","description":"Method to extract from markdown files","line":85},{"name":"_extract_yaml","description":"Method to extract from YAML files","line":135},{"name":"_extract_json","description":"Method to extract from JSON files","line":164},{"name":"_extract_text","description":"Method to extract from text files","line":193}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Content Extractor Module","description":"Module for extracting content from various document types","last_updated":"2023-03-11","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":22,"line_end":28},
# {"name":"ContentExtractor Class","description":"Main class for content extraction","line_start":31,"line_end":165},
# {"name":"extract Method","description":"Main extraction method","line_start":42,"line_end":68},
# {"name":"_extract_markdown Method","description":"Method to extract from markdown files","line_start":70,"line_end":96},
# {"name":"_extract_yaml Method","description":"Method to extract from YAML files","line_start":98,"line_end":119},
# {"name":"_extract_json Method","description":"Method to extract from JSON files","line_start":121,"line_end":142},
# {"name":"_extract_text Method","description":"Method to extract from text files","line_start":144,"line_end":165}
# ],
# "key_elements":[
# {"name":"ContentExtractor","description":"Main content extraction class","line":31},
# {"name":"extract","description":"Main extraction method","line":42}
# ]
# }
# FILE_MAP_END

"""
Content Extractor Module for Documentation Rule Generator.

This module provides functionality to extract content from various document types.
"""

import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Extracts structured content from various document types.
    """

    def __init__(self):
        """
        Initialize the content extractor.
        """
        logger.info("Initialized ContentExtractor")

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract content from a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing extracted content
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return {}

        # Determine file type based on extension
        extension = file_path.suffix.lower()

        try:
            # Extract based on file type
            if extension == ".md":
                return self._extract_markdown(file_path)
            elif extension in [".yaml", ".yml"]:
                return self._extract_yaml(file_path)
            elif extension == ".json":
                return self._extract_json(file_path)
            else:
                return self._extract_text(file_path)

        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {str(e)}")
            return {}

    def _extract_markdown(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract content from a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            Dictionary containing extracted content
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            result = {
                "file_path": str(file_path),
                "text": text,
                "content": text,
                "timestamp": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(),
                "format": "markdown",
                "status": "success",
            }

            # Extract title from first header
            lines = text.strip().split("\n")
            for line in lines:
                if line.startswith("#"):
                    title = line.lstrip("#").strip()
                    result["title"] = title
                    break

            # Get metadata from file if available
            # Markdown files often have YAML front matter
            if text.startswith("---"):
                try:
                    # Find the end of the YAML front matter
                    end_index = text.find("---", 3)
                    if end_index > 0:
                        front_matter = text[3:end_index].strip()
                        metadata = yaml.safe_load(front_matter)
                        result["metadata"] = metadata
                except Exception as e:
                    logger.warning(
                        f"Error parsing front matter in {file_path}: {str(e)}"
                    )

            return result

        except Exception as e:
            logger.error(f"Error extracting from markdown file {file_path}: {str(e)}")
            return {"file_path": str(file_path), "error": str(e)}

    def _extract_yaml(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract content from a YAML file.

        Args:
            file_path: Path to the YAML file

        Returns:
            Dictionary containing extracted content
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                yaml_text = f.read()

            import yaml

            yaml_data = yaml.safe_load(yaml_text)

            return {
                "file_path": str(file_path),
                "content": yaml_data,
                "text": yaml_text,
                "timestamp": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(),
                "format": "yaml",
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Error extracting YAML content: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _extract_json(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract content from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Dictionary containing extracted content
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json_text = f.read()

            import json

            json_data = json.loads(json_text)

            return {
                "file_path": str(file_path),
                "content": json_data,
                "text": json_text,
                "timestamp": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(),
                "format": "json",
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Error extracting JSON content: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _extract_text(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract content from a text file.

        Args:
            file_path: Path to the text file

        Returns:
            Dictionary containing extracted content
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            return {
                "file_path": str(file_path),
                "content": text,
                "text": text,
                "timestamp": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(),
                "format": "text",
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Error extracting text content: {str(e)}")
            return {"status": "error", "error": str(e)}
