# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"File Scanner Module","description":"Module for scanning directories for documentation files","last_updated":"2023-03-10","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":22,"line_end":27},{"name":"FileScanner Class","description":"Main class for file scanning","line_start":30,"line_end":78}],"key_elements":[{"name":"FileScanner","description":"Main class for scanning directories","line":30},{"name":"__init__","description":"Initializer for the FileScanner class","line":37},{"name":"scan","description":"Main scanning method","line":48}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"File Scanner Module","description":"Module for scanning directories for documentation files","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":22,"line_end":27},
# {"name":"FileScanner Class","description":"Main class for file scanning","line_start":30,"line_end":78}
# ],
# "key_elements":[
# {"name":"FileScanner","description":"Main class for scanning directories","line":30},
# {"name":"scan","description":"Main scanning method","line":44}
# ]
# }
# FILE_MAP_END

"""
File Scanner Module for Documentation Rule Generator.

This module provides functionality to scan directories for documentation files.
"""

import logging
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FileScanner:
    """
    Scans a directory for documentation files.
    """

    def __init__(self, base_dir: Path, extensions: List[str]):
        """
        Initialize the file scanner.

        Args:
            base_dir: Base directory to scan
            extensions: List of file extensions to scan for
        """
        self.base_dir = base_dir
        self.extensions = extensions

    def scan(self) -> List[Path]:
        """
        Scan for files with the specified extensions.

        Returns:
            List of file paths
        """
        files = []

        logger.info(
            f"Scanning directory {self.base_dir} for files with extensions: {self.extensions}"
        )

        try:
            # Check if base directory exists
            if not self.base_dir.exists():
                logger.error(f"Base directory {self.base_dir} does not exist")
                return []

            # Scan for each extension
            for ext in self.extensions:
                pattern = f"**/*{ext}"
                found_files = list(self.base_dir.glob(pattern))
                logger.debug(f"Found {len(found_files)} files with extension {ext}")
                files.extend(found_files)

            # Log results
            logger.info(f"Found {len(files)} total files")

            # Remove duplicates and sort
            unique_files = list(set(files))
            unique_files.sort()

            return unique_files

        except Exception as e:
            logger.error(f"Error scanning for files: {str(e)}")
            return []
