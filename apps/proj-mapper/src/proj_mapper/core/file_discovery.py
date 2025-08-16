"""File discovery module.

This module provides functionality for discovering and categorizing files in a project.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import fnmatch

from proj_mapper.models.file import DiscoveredFile, FileType
from proj_mapper.utils.gitignore import GitignoreParser

# Configure logging
logger = logging.getLogger(__name__)


class FileDiscovery:
    """Discovers and categorizes files in a project."""

    # Default file patterns to include
    DEFAULT_INCLUDE_PATTERNS = {
        "*.py",  # Python files
        "*.js",  # JavaScript files
        "*.ts",  # TypeScript files
        "*.md",  # Markdown files
        "*.rst",  # reStructuredText files
    }

    # Default patterns to exclude
    DEFAULT_EXCLUDE_PATTERNS = {
        "**/venv/**",  # Virtual environments
        "**/__pycache__/**",  # Python cache
        "**/node_modules/**",  # Node.js modules
        "**/.git/**",  # Git directory
        "**/.svn/**",  # SVN directory
        "**/.hg/**",  # Mercurial directory
        "**/build/**",  # Build directories
        "**/dist/**",  # Distribution directories
        "**/.tox/**",  # Tox test environments
        "**/.eggs/**",  # Python egg directories
        "**/*.pyc",  # Python compiled files
        "**/*.pyo",  # Python optimized files
        "**/*.pyd",  # Python DLL files
        "**/*.so",  # Shared libraries
        "**/*.dll",  # DLL files
        "**/*.exe",  # Executable files
    }

    # Maximum file size in bytes (default: 10MB)
    DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(
        self,
        include_patterns: Optional[Set[str]] = None,
        exclude_patterns: Optional[Set[str]] = None,
        max_file_size: Optional[int] = None,
        respect_gitignore: bool = True,
        project_root: Optional[Path] = None,
    ):
        """Initialize the file discovery.

        Args:
            include_patterns: Set of glob patterns for files to include
            exclude_patterns: Set of glob patterns for files to exclude
            max_file_size: Maximum file size in bytes
            respect_gitignore: Whether to respect .gitignore files
            project_root: Project root directory for gitignore parsing
        """
        self.include_patterns = include_patterns or self.DEFAULT_INCLUDE_PATTERNS
        self.exclude_patterns = exclude_patterns or self.DEFAULT_EXCLUDE_PATTERNS
        self.max_file_size = max_file_size or self.DEFAULT_MAX_FILE_SIZE
        self.respect_gitignore = respect_gitignore
        self.project_root = project_root
        self.gitignore_parser: Optional[GitignoreParser] = None

        logger.debug(f"Initialized FileDiscovery with:")
        logger.debug(f"  Include patterns: {self.include_patterns}")
        logger.debug(f"  Exclude patterns: {self.exclude_patterns}")
        logger.debug(f"  Max file size: {self.max_file_size} bytes")
        logger.debug(f"  Respect gitignore: {self.respect_gitignore}")

    def discover_files(self, root_path: Path) -> List[DiscoveredFile]:
        """Discover files in a directory.

        Args:
            root_path: Path to the root directory

        Returns:
            List of discovered files
        """
        logger.info(f"Discovering files in: {root_path}")
        discovered_files = []

        # Convert root path to absolute path
        root_path = Path(root_path).resolve()
        logger.debug(f"Resolved root path: {root_path}")
        logger.debug(f"Include patterns: {self.include_patterns}")
        logger.debug(f"Exclude patterns: {self.exclude_patterns}")

        # Initialize gitignore parser if enabled
        if self.respect_gitignore:
            project_root = self.project_root or root_path
            self.gitignore_parser = GitignoreParser(project_root)
            logger.info(
                f"Initialized gitignore parser with {len(self.gitignore_parser.patterns)} patterns"
            )

        # Walk the directory tree
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Convert to Path objects
            current_dir = Path(dirpath)
            logger.debug(f"\nScanning directory: {current_dir}")
            logger.debug(f"Found {len(filenames)} files in directory")

            # Skip excluded directories
            original_dirnames = dirnames.copy()
            dirnames[:] = [
                d
                for d in dirnames
                if not any(
                    self._matches_pattern(str(current_dir / d), str(root_path), pattern)
                    for pattern in self.exclude_patterns
                )
            ]

            # Apply gitignore filtering to directories
            if self.gitignore_parser:
                original_dirnames_after_exclude = dirnames.copy()
                dirnames[:] = [
                    d
                    for d in dirnames
                    if not self.gitignore_parser.should_ignore(current_dir / d)
                ]
                gitignore_skipped_dirs = set(original_dirnames_after_exclude) - set(
                    dirnames
                )
                if gitignore_skipped_dirs:
                    logger.debug(
                        f"Gitignore skipped directories: {gitignore_skipped_dirs}"
                    )

            # Log skipped directories
            skipped_dirs = set(original_dirnames) - set(dirnames)
            if skipped_dirs:
                logger.debug(f"Skipped excluded directories: {skipped_dirs}")

            # Process files
            for filename in filenames:
                file_path = current_dir / filename
                logger.debug(f"\nChecking file: {file_path}")

                # Get relative path for pattern matching
                relative_path = str(file_path.relative_to(root_path))
                logger.debug(f"Relative path: {relative_path}")

                # Skip if file matches exclude patterns
                if any(
                    self._matches_pattern(relative_path, str(root_path), pattern)
                    for pattern in self.exclude_patterns
                ):
                    logger.debug(f"Skipped excluded file: {file_path}")
                    continue

                # Skip if file matches gitignore patterns
                if self.gitignore_parser and self.gitignore_parser.should_ignore(
                    file_path
                ):
                    logger.debug(f"Gitignore skipped file: {file_path}")
                    continue

                # Skip if file doesn't match include patterns
                if not any(
                    self._matches_pattern(relative_path, str(root_path), pattern)
                    for pattern in self.include_patterns
                ):
                    logger.debug(
                        f"Skipped non-matching file: {file_path} (does not match any include patterns)"
                    )
                    continue

                try:
                    # Create discovered file
                    discovered_file = DiscoveredFile.from_path(file_path, root_path)

                    # Skip if file is too large
                    if discovered_file.size > self.max_file_size:
                        logger.warning(
                            f"Skipping large file: {file_path} ({discovered_file.size} bytes)"
                        )
                        continue

                    discovered_files.append(discovered_file)
                    logger.debug(f"Added file: {file_path}")
                    logger.debug(f"  Type: {discovered_file.file_type.value}")
                    logger.debug(f"  Size: {discovered_file.size} bytes")
                    logger.debug(f"  Is binary: {discovered_file.is_binary}")

                except Exception as e:
                    logger.error(f"Error accessing file {file_path}: {e}")

        logger.info(f"Discovered {len(discovered_files)} files")
        logger.debug("Files by type:")
        type_counts = {}
        for file in discovered_files:
            file_type = file.file_type.value
            if file_type not in type_counts:
                type_counts[file_type] = 0
            type_counts[file_type] += 1
        for file_type, count in type_counts.items():
            logger.debug(f"  {file_type}: {count}")

        return discovered_files

    def categorize_files(
        self,
        files: List[DiscoveredFile],
    ) -> Dict[str, List[DiscoveredFile]]:
        """Categorize files by type.

        Args:
            files: List of discovered files

        Returns:
            Dictionary mapping file type strings to lists of files
        """
        logger.debug("Categorizing files by type")
        categorized: Dict[str, List[DiscoveredFile]] = {}

        for file in files:
            # Use the string value of file_type as the key
            file_type_str = file.file_type.value
            if file_type_str not in categorized:
                categorized[file_type_str] = []
            categorized[file_type_str].append(file)

        for file_type, type_files in categorized.items():
            if type_files:
                logger.debug(f"Found {len(type_files)} {file_type} files")

        return categorized

    @staticmethod
    def _matches_pattern(path: str, root: str, pattern: str) -> bool:
        """Check if a path matches a glob pattern.

        Args:
            path: Path to check (relative to root)
            root: Root directory path
            pattern: Glob pattern

        Returns:
            True if the path matches the pattern
        """
        # Convert pattern to use OS-specific path separators
        pattern = pattern.replace("/", os.sep).replace("\\", os.sep)

        # Handle '**' patterns
        if "**" in pattern:
            # Split pattern into parts
            parts = pattern.split("**")

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Checking complex pattern match: {path} against {pattern}"
                )
                logger.debug(f"Pattern parts: {parts}")

            # Check if path matches all parts in sequence
            current_path = path
            for part in parts:
                if part:
                    # Find the part in the remaining path
                    if not fnmatch.fnmatch(current_path, f"*{part}*"):
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(
                                f"  Pattern part '{part}' did not match in '{current_path}'"
                            )
                        return False
                    # Update remaining path
                    idx = current_path.find(part)
                    if idx >= 0:
                        current_path = current_path[idx + len(part) :]
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(
                                f"  Matched part '{part}', remaining path: '{current_path}'"
                            )

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"  Complex pattern match result: True")
            return True

        # For simple patterns, use direct matching
        result = fnmatch.fnmatch(path, pattern)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Simple pattern match: {path} against {pattern} -> {result}")
        return result

    @staticmethod
    def _is_binary(path: Path) -> bool:
        """Check if a file is likely binary.

        Args:
            path: Path to check

        Returns:
            True if the file is likely binary, False otherwise
        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Checking if file is binary: {path}")

        # Skip check for directories
        if path.is_dir():
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"  {path} is a directory, not binary")
            return False

        # Common binary extensions
        binary_extensions = {
            ".pyc",
            ".pyd",
            ".so",
            ".dll",
            ".exe",
            ".bin",
            ".dat",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".ico",
            ".tif",
            ".tiff",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".mkv",
            ".wav",
            ".flac",
            ".pdf",
            ".doc",
            ".docx",
            ".ppt",
            ".pptx",
            ".xls",
            ".xlsx",
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".7z",
            ".rar",
        }

        if path.suffix.lower() in binary_extensions:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"  {path} has binary extension {path.suffix}, classified as binary"
                )
            return True

        # Check file content
        try:
            # Read first 8KB of the file
            chunk_size = 8192
            with open(path, "rb") as f:
                chunk = f.read(chunk_size)

            # Check for null bytes which often indicate binary
            if b"\x00" in chunk:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"  {path} contains null bytes, classified as binary")
                return True

            # Try decoding as UTF-8
            try:
                chunk.decode("utf-8")
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"  {path} can be decoded as UTF-8, classified as text"
                    )
                return False
            except UnicodeDecodeError:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"  {path} cannot be decoded as UTF-8, classified as binary"
                    )
                return True

        except (IOError, OSError) as e:
            # If we can't read the file, assume it's binary
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"  Error reading {path}: {e}, classified as binary")
            return True

        return False
