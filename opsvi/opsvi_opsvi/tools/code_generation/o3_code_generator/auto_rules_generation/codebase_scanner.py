"""
Codebase Scanner Component

Discovers and categorizes all Python files in the codebase, extracting metadata
and identifying file relationships and dependencies.

Enhanced with comprehensive debug logging, progress indicators, timing information,
step-by-step logging for file discovery, metadata extraction, and scanning phases.
Includes progress counters for loop iterations and timeout mechanisms to prevent
infinite loops.
"""

import ast
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)

# Default timeout for scanning loops in seconds
SCAN_TIMEOUT_SECONDS = 300  # 5 minutes


@dataclass
class FileMetadata:
    """Metadata for a single Python file."""

    path: Path
    size: int
    last_modified: datetime
    category: str
    import_dependencies: set[str]
    has_main: bool
    has_classes: bool
    has_functions: bool
    line_count: int
    complexity_score: float


@dataclass
class CodebaseMetadata:
    """Complete codebase analysis metadata."""

    total_files: int
    total_lines: int
    categories: dict[str, list[FileMetadata]]
    dependencies: dict[str, set[str]]
    file_relationships: dict[str, list[str]]


class CodebaseScanner:
    """
    Scans the codebase to discover and categorize Python files.

    Walks through directories recursively, categorizes files, extracts metadata,
    and identifies file relationships and dependencies.
    """

    def __init__(self, base_path: Path | None = None) -> None:
        """
        Initialize the codebase scanner.

        Attributes:
            base_path: Root path for codebase scan.
            logger: O3Logger instance for logging.
            directory_manager: DirectoryManager instance for directory operations.
            categories: Predefined file categories.
            scan_timeout: Maximum allowed time (in seconds) for scanning loops.
        """
        setup_logger(LogConfig())
        self.logger = get_logger()

        self.base_path = base_path or Path("src/applications/oamat_sd")
        self.directory_manager = DirectoryManager()
        self.scan_timeout = SCAN_TIMEOUT_SECONDS

        try:
            self.directory_manager.ensure_directory_exists(self.base_path)
        except Exception as e:
            self.logger.log_error(f"Failed to ensure base directory exists: {e}")
            raise

        # Predefined file categories
        self.categories: dict[str, list[Path]] = {
            "main_scripts": [],
            "modules": [],
            "utils": [],
            "tests": [],
            "configs": [],
            "docs": [],
            "other": [],
        }

        self.logger.log_info(f"Initialized CodebaseScanner for path: {self.base_path}")

    def scan_codebase(self) -> CodebaseMetadata:
        """
        Perform complete codebase scan.

        Returns:
            CodebaseMetadata: Complete analysis of the codebase.
        """
        overall_start = time.monotonic()
        self.logger.log_info("Starting codebase scan...")

        if not self.base_path.exists():
            self.logger.log_error(f"Base path does not exist: {self.base_path}")
            raise FileNotFoundError(f"Base path does not exist: {self.base_path}")

        # File discovery phase
        discovery_start = time.monotonic()
        python_files = self._discover_python_files()
        discovery_duration = time.monotonic() - discovery_start
        self.logger.log_info(
            f"Discovered {len(python_files)} Python files in {discovery_duration:.2f} seconds"
        )

        # Categorization phase
        categorization_start = time.monotonic()
        categorized_files = self._categorize_files(python_files)
        categorization_duration = time.monotonic() - categorization_start
        self.logger.log_info(
            f"Categorized files in {categorization_duration:.2f} seconds"
        )

        # Metadata extraction phase
        metadata_start = time.monotonic()
        file_metadata = self._extract_file_metadata(categorized_files)
        metadata_duration = time.monotonic() - metadata_start
        self.logger.log_info(
            f"Extracted metadata for files in {metadata_duration:.2f} seconds"
        )

        # Dependency analysis phase
        dependency_start = time.monotonic()
        dependencies = self._analyze_dependencies(file_metadata)
        dependency_duration = time.monotonic() - dependency_start
        self.logger.log_debug(
            f"Analyzed dependencies in {dependency_duration:.2f} seconds"
        )

        # Relationships analysis phase
        relationship_start = time.monotonic()
        relationships = self._analyze_file_relationships(file_metadata)
        relationship_duration = time.monotonic() - relationship_start
        self.logger.log_debug(
            f"Analyzed file relationships in {relationship_duration:.2f} seconds"
        )

        # Prepare categories using metadata
        categories_with_metadata = {}
        for category, file_paths in categorized_files.items():
            categories_with_metadata[category] = [
                file_metadata[path] for path in file_paths if path in file_metadata
            ]

        total_files = len(python_files)
        total_lines = sum(meta.line_count for meta in file_metadata.values())
        overall_duration = time.monotonic() - overall_start
        self.logger.log_info(
            f"Codebase scan complete: {total_files} files, {total_lines} lines in {overall_duration:.2f} seconds"
        )

        return CodebaseMetadata(
            total_files=total_files,
            total_lines=total_lines,
            categories=categories_with_metadata,
            dependencies=dependencies,
            file_relationships=relationships,
        )

    def _discover_python_files(self) -> list[Path]:
        """
        Discover all Python files in the codebase.

        Returns:
            List[Path]: All .py file paths under base_path.
        """
        start_time = time.monotonic()
        python_files: list[Path] = []
        file_counter = 0

        # Walk the file system with infinite loop prevention via timeout
        for root, dirs, files in os.walk(self.base_path):
            current_elapsed = time.monotonic() - start_time
            if current_elapsed > self.scan_timeout:
                self.logger.log_error("Timeout reached during file discovery")
                raise TimeoutError("File discovery exceeded allowed time.")
            # Filter out unwanted directories
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in {"__pycache__", "node_modules", "venv"}
            ]
            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)
                    file_counter += 1
                    if file_counter % 100 == 0:
                        self.logger.log_debug(
                            f"Discovered {file_counter} Python files so far"
                        )
        self.logger.log_debug(
            f"Final count after discovery: {file_counter} Python files"
        )
        return python_files

    def _categorize_files(self, python_files: list[Path]) -> dict[str, list[Path]]:
        """
        Categorize Python files based on their location and content.

        Args:
            python_files: List of file paths to categorize.

        Returns:
            Dict[str, List[Path]]: Mapping from category to list of paths.
        """
        categorized: dict[str, list[Path]] = {cat: [] for cat in self.categories.keys()}
        file_counter = 0
        start_time = time.monotonic()

        for file_path in python_files:
            current_elapsed = time.monotonic() - start_time
            if current_elapsed > self.scan_timeout:
                self.logger.log_error("Timeout reached during file categorization")
                raise TimeoutError("File categorization exceeded allowed time.")
            relative_path = file_path.relative_to(self.base_path)
            path_parts = relative_path.parts
            category = self._determine_file_category(file_path, path_parts)
            categorized[category].append(file_path)
            file_counter += 1
            if file_counter % 100 == 0:
                self.logger.log_debug(f"Categorized {file_counter} files so far")
        self.logger.log_debug(
            f"Final categorization count: {file_counter} files categorized"
        )
        return categorized

    def _determine_file_category(
        self, file_path: Path, path_parts: tuple[str, ...]
    ) -> str:
        """
        Determine the category of a file based on its path and content.

        Args:
            file_path: Path of the file.
            path_parts: Tuple of path components relative to base_path.

        Returns:
            str: Category name.
        """
        filename = file_path.name.lower()
        if any(
            part in {"test", "tests", "testing"} for part in path_parts
        ) or filename.startswith("test_"):
            return "tests"
        if any(part in {"utils", "utilities", "helpers"} for part in path_parts):
            return "utils"
        if any(
            part in {"config", "conf", "settings"} for part in path_parts
        ) or filename in {"config.py", "settings.py"}:
            return "configs"
        if any(part in {"docs", "documentation"} for part in path_parts):
            return "docs"
        if filename in {"main.py", "__main__.py"} or "main" in path_parts:
            return "main_scripts"
        return "modules"

    def _extract_file_metadata(
        self, categorized_files: dict[str, list[Path]]
    ) -> dict[Path, FileMetadata]:
        """
        Extract detailed metadata for each file.

        Args:
            categorized_files: Mapping of categories to file paths.

        Returns:
            Dict[Path, FileMetadata]: Mapping of file path to its metadata.
        """
        file_metadata: dict[Path, FileMetadata] = {}
        total_files = sum(len(files) for files in categorized_files.values())
        processed_files = 0
        start_time = time.monotonic()

        for category, files in categorized_files.items():
            for file_path in files:
                current_elapsed = time.monotonic() - start_time
                if current_elapsed > self.scan_timeout:
                    self.logger.log_error("Timeout reached during metadata extraction")
                    raise TimeoutError("Metadata extraction exceeded allowed time.")
                try:
                    metadata = self._extract_single_file_metadata(file_path, category)
                    file_metadata[file_path] = metadata
                except Exception as e:
                    self.logger.log_error(
                        f"Failed to extract metadata for {file_path}: {e}"
                    )
                    raise
                processed_files += 1
                if processed_files % 50 == 0:
                    self.logger.log_debug(
                        f"Extracted metadata for {processed_files}/{total_files} files"
                    )
        self.logger.log_debug(
            f"Completed metadata extraction for {processed_files} files"
        )
        return file_metadata

    def _extract_single_file_metadata(
        self, file_path: Path, category: str
    ) -> FileMetadata:
        """
        Extract metadata for a single file.

        Args:
            file_path: Path of the file.
            category: Category of the file.

        Returns:
            FileMetadata: Extracted metadata.
        """
        stat = file_path.stat()
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            self.logger.log_debug(f"SyntaxError encountered when parsing {file_path}")
            tree = None

        import_dependencies = self._extract_import_dependencies(tree) if tree else set()
        has_main = self._has_main_function(tree) if tree else False
        has_classes = self._has_classes(tree) if tree else False
        has_functions = self._has_functions(tree) if tree else False
        line_count = len(content.splitlines())
        complexity_score = self._calculate_complexity_score(tree) if tree else 0.0

        return FileMetadata(
            path=file_path,
            size=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            category=category,
            import_dependencies=import_dependencies,
            has_main=has_main,
            has_classes=has_classes,
            has_functions=has_functions,
            line_count=line_count,
            complexity_score=complexity_score,
        )

    def _extract_import_dependencies(self, tree: ast.AST) -> set[str]:
        """
        Extract import dependencies from AST.

        Args:
            tree: Parsed AST of the file.

        Returns:
            Set[str]: Set of module names imported.
        """
        dependencies: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                dependencies.add(node.module)
        self.logger.log_debug(f"Extracted dependencies: {dependencies}")
        return dependencies

    def _has_main_function(self, tree: ast.AST) -> bool:
        """
        Check if file has a main function.

        Args:
            tree: Parsed AST.

        Returns:
            bool: True if main() is defined.
        """
        return any(
            isinstance(node, ast.FunctionDef) and node.name == "main"
            for node in ast.walk(tree)
        )

    def _has_classes(self, tree: ast.AST) -> bool:
        """
        Check if file has class definitions.

        Args:
            tree: Parsed AST.

        Returns:
            bool: True if any class is defined.
        """
        return any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))

    def _has_functions(self, tree: ast.AST) -> bool:
        """
        Check if file has function definitions.

        Args:
            tree: Parsed AST.

        Returns:
            bool: True if any function is defined.
        """
        return any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))

    def _calculate_complexity_score(self, tree: ast.AST) -> float:
        """
        Calculate a simple complexity score based on AST nodes.

        Args:
            tree: Parsed AST.

        Returns:
            float: Complexity score.
        """
        complexity = 0.0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                complexity += 1.0
            elif isinstance(node, ast.FunctionDef):
                complexity += 0.5
            elif isinstance(node, ast.ClassDef):
                complexity += 1.0
        return complexity

    def _analyze_dependencies(
        self, file_metadata: dict[Path, FileMetadata]
    ) -> dict[str, set[str]]:
        """
        Analyze dependencies between files.

        Args:
            file_metadata: Mapping of file paths to metadata.

        Returns:
            Dict[str, Set[str]]: Mapping of file to imported modules.
        """
        dependencies: dict[str, set[str]] = {}
        for file_path, metadata in file_metadata.items():
            file_key = str(file_path.relative_to(self.base_path))
            dependencies[file_key] = metadata.import_dependencies
        self.logger.log_debug(
            f"Dependencies analysis completed for {len(dependencies)} files"
        )
        return dependencies

    def _analyze_file_relationships(
        self, file_metadata: dict[Path, FileMetadata]
    ) -> dict[str, list[str]]:
        """
        Analyze relationships between files based on imports.

        Args:
            file_metadata: Mapping of file paths to metadata.

        Returns:
            Dict[str, List[str]]: Mapping of file to list of dependent files.
        """
        relationships: dict[str, list[str]] = {}
        for file_path, metadata in file_metadata.items():
            file_key = str(file_path.relative_to(self.base_path))
            related: list[str] = []
            for other_path, other_meta in file_metadata.items():
                if file_path == other_path:
                    continue
                other_key = str(other_path.relative_to(self.base_path))
                # Check if the normalized file_key appears in the import dependencies of the other file.
                normalized_file_key = file_key.replace(".py", "").replace("/", ".")
                if normalized_file_key in other_meta.import_dependencies:
                    related.append(other_key)
            relationships[file_key] = related
        self.logger.log_debug(
            f"File relationship analysis completed for {len(relationships)} files"
        )
        return relationships
