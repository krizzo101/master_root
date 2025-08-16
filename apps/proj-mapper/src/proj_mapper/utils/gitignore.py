"""Gitignore pattern parsing and matching utilities."""

import logging
import os
import re
from pathlib import Path
from typing import List, Set, Optional
import fnmatch

logger = logging.getLogger(__name__)


class GitignoreParser:
    """Parse and match .gitignore patterns."""

    def __init__(self, project_root: Path):
        """Initialize with project root directory."""
        self.project_root = Path(project_root).resolve()
        self.patterns: List[str] = []
        self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> None:
        """Load patterns from .gitignore files in the project."""
        # Load from root .gitignore
        root_gitignore = self.project_root / ".gitignore"
        if root_gitignore.exists():
            logger.debug(f"Loading patterns from {root_gitignore}")
            self.patterns.extend(self._parse_gitignore_file(root_gitignore))

        # Load from .ignore (alternative)
        root_ignore = self.project_root / ".ignore"
        if root_ignore.exists():
            logger.debug(f"Loading patterns from {root_ignore}")
            self.patterns.extend(self._parse_gitignore_file(root_ignore))

        # Load from subdirectory .gitignore files
        for gitignore_file in self.project_root.rglob(".gitignore"):
            if gitignore_file != root_gitignore:
                logger.debug(f"Loading patterns from {gitignore_file}")
                self.patterns.extend(self._parse_gitignore_file(gitignore_file))

        logger.info(f"Loaded {len(self.patterns)} gitignore patterns")

    def _parse_gitignore_file(self, gitignore_path: Path) -> List[str]:
        """Parse a .gitignore file and return patterns."""
        patterns = []
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Handle .gitignore syntax
                        pattern = self._normalize_gitignore_pattern(
                            line, gitignore_path
                        )
                        if pattern:
                            patterns.append(pattern)
        except Exception as e:
            logger.warning(f"Failed to parse {gitignore_path}: {e}")
        return patterns

    def _normalize_gitignore_pattern(
        self, pattern: str, gitignore_path: Path
    ) -> Optional[str]:
        """Normalize .gitignore pattern to glob pattern."""
        # Handle .gitignore specific syntax
        if pattern.startswith("!"):
            # Negation - convert to positive pattern
            pattern = pattern[1:]

        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            pattern = pattern[:-1] + "/**"

        # Handle absolute patterns (starting with /)
        if pattern.startswith("/"):
            pattern = pattern[1:]

        # Handle directory patterns without trailing slash (like .venv, venv)
        # These should match the directory and all its contents
        if (
            not pattern.endswith("/**")
            and not pattern.endswith("/")
            and not pattern.endswith("*")
        ):
            pattern = pattern + "/**"

        # Convert to relative path from project root
        if gitignore_path.parent != self.project_root:
            relative_path = gitignore_path.parent.relative_to(self.project_root)
            pattern = f"{relative_path}/{pattern}"

        return pattern

    def should_ignore(self, file_path: Path) -> bool:
        """Check if a file should be ignored based on .gitignore patterns."""
        if not self.patterns:
            return False

        # Get relative path from project root
        try:
            relative_path = file_path.relative_to(self.project_root)
            relative_str = str(relative_path).replace(os.sep, "/")
        except ValueError:
            # File is outside project root
            return False

        # Check against patterns
        for pattern in self.patterns:
            # Direct pattern match
            if fnmatch.fnmatch(relative_str, pattern):
                return True

        return False


def load_gitignore_patterns(project_root: Path) -> List[str]:
    """Load gitignore patterns from project root."""
    parser = GitignoreParser(project_root)
    return parser.patterns


def should_ignore_path(file_path: Path, project_root: Path) -> bool:
    """Check if a file should be ignored based on .gitignore patterns."""
    parser = GitignoreParser(project_root)
    return parser.should_ignore(file_path)
