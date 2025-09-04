"""Enhanced code source adapter with advanced repository analysis and real-time monitoring.

This adapter extends the base code adapter with:
- Advanced AST parsing for multiple languages
- Real-time file watching and incremental updates
- Symbol indexing and cross-file relationship detection
- Git integration for change tracking
- Parallel processing for large codebases
- Architectural pattern detection
- Quality metrics calculation
"""

import ast
import asyncio
import hashlib
import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Union

import structlog

from ...models.common import ContextItem
from ..base_adapter import AdapterConfig, BaseAdapter, BatchMode
from ..transformers import DataTransformer
from .code_adapter import CodeAdapter

logger = structlog.get_logger(__name__)


class EnhancedCodeAdapter(CodeAdapter):
    """Enhanced code adapter with advanced analysis capabilities."""

    @classmethod
    def default_config(cls) -> AdapterConfig:
        """Get enhanced default configuration."""
        config = super().default_config()

        # Enhanced configuration options
        config.source_config.update(
            {
                # Advanced parsing options
                "enable_advanced_analysis": True,
                "build_dependency_graph": True,
                "calculate_metrics": True,
                "detect_design_patterns": True,
                "analyze_complexity": True,
                "extract_variables": True,
                "extract_constants": True,
                "extract_docstrings": True,
                "extract_decorators": True,
                "extract_type_hints": True,
                # Performance options
                "parallel_processing": True,
                "max_worker_threads": 4,
                "batch_process_files": True,
                "cache_analysis_results": True,
                # Real-time monitoring
                "enable_file_watching": True,
                "enable_incremental_scan": True,
                "immediate_reanalysis": False,
                "watch_git_changes": True,
                # Git integration
                "use_git_tracking": True,
                "track_git_history": True,
                "analyze_git_blame": True,
                "max_git_history": 20,
                # Quality thresholds
                "complexity_threshold": 10,
                "documentation_threshold": 0.7,
                "maintainability_threshold": 0.6,
                # Language-specific options
                "python_ast_full_analysis": True,
                "javascript_babel_parsing": False,
                "typescript_compiler_api": False,
            }
        )

        return config

    def __init__(self, config: AdapterConfig):
        """Initialize enhanced code adapter."""
        super().__init__(config)

        # Enhanced state management
        self._symbol_index: Dict[str, List[Dict[str, Any]]] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._file_watcher_active = False
        self._incremental_enabled = False
        self._last_scan_time: Optional[datetime] = None
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}
        self._git_integration_active = False

        # Thread pool for parallel processing
        self._thread_pool = None
        if config.source_config.get("parallel_processing", True):
            max_workers = config.source_config.get("max_worker_threads", 4)
            self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)

        # Quality metrics tracking
        self._quality_metrics = {
            "total_files_analyzed": 0,
            "high_complexity_files": 0,
            "low_documentation_files": 0,
            "pattern_detections": {},
        }

    async def initialize(self) -> None:
        """Initialize enhanced code adapter with all features."""
        await super().initialize()

        # Initialize symbol index and dependency tracking
        if self.config.source_config.get("build_dependency_graph", True):
            await self._initialize_symbol_index()

        # Set up incremental scanning if enabled
        if self.config.source_config.get("enable_incremental_scan", True):
            self._incremental_enabled = True
            self.logger.info("Incremental scanning enabled")

        # Initialize git integration if available
        if self.config.source_config.get("use_git_tracking", True):
            await self._initialize_git_integration()

        # Start file watcher if enabled
        if self.config.source_config.get("enable_file_watching", True):
            await self.start_file_watcher()

        self.logger.info(
            "Enhanced code adapter initialized",
            features={
                "incremental_enabled": self._incremental_enabled,
                "file_watcher": self._file_watcher_active,
                "git_integration": self._git_integration_active,
                "parallel_processing": self._thread_pool is not None,
                "advanced_analysis": self.config.source_config.get(
                    "enable_advanced_analysis", True
                ),
            },
        )

    async def fetch_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Enhanced fetch with parallel processing and caching."""
        self._last_scan_time = datetime.now()

        # Use incremental fetching if enabled and since parameter provided
        if (
            self._incremental_enabled
            and since
            and self.config.source_config.get("enable_incremental_scan", True)
        ):
            async for item in self._fetch_incremental_items(since, until, limit):
                yield item
        else:
            # Full scan with enhanced processing
            async for item in self._fetch_enhanced_items(since, until, limit):
                yield item

        # Update quality metrics
        await self._update_quality_metrics()

    async def _fetch_enhanced_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch items with enhanced processing."""
        count = 0

        # First, yield .proj-intel data if enabled
        if self.config.source_config.get("enable_proj_intel", True):
            async for intel_item in self._fetch_proj_intel_items(since, until):
                if limit and count >= limit:
                    return
                yield intel_item
                count += 1

        # Process regular files with parallel analysis
        scan_dirs = self.config.source_config.get("scan_directories", ["."])
        include_patterns = self.config.source_config.get("include_patterns", ["*"])
        exclude_patterns = self.config.source_config.get("exclude_patterns", [])
        max_size_mb = self.config.source_config.get("max_file_size_mb", 10)

        # Collect all files first for batch processing
        files_to_process = []
        for directory in scan_dirs:
            async for file_info in self._scan_directory_enhanced(
                directory, include_patterns, exclude_patterns, max_size_mb, since, until
            ):
                files_to_process.append(file_info)

        # Process files in parallel batches
        if (
            self.config.source_config.get("batch_process_files", True)
            and self._thread_pool
        ):
            async for item in self._process_files_parallel(
                files_to_process, limit - count if limit else None
            ):
                yield item
                count += 1
                if limit and count >= limit:
                    break
        else:
            # Sequential processing
            for file_info in files_to_process:
                if limit and count >= limit:
                    break

                item = await self._process_single_file_enhanced(file_info)
                if item:
                    yield item
                    count += 1

    async def _fetch_incremental_items(
        self,
        since: datetime,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch only changed items since the given timestamp."""
        self.logger.info(f"Fetching incremental items since {since}")

        # Get changed files from git if available
        if self._git_integration_active:
            git_changes = await self.get_recent_git_changes(since_hours=24)
            changed_files = set()

            for change in git_changes:
                for file_info in change.get("files", []):
                    changed_files.add(file_info["path"])
        else:
            # Fallback to filesystem modification times
            changed_files = set(self.get_changed_files_since(since))

        # Process changed files
        count = 0
        for file_path in changed_files:
            if limit and count >= limit:
                break

            path_obj = Path(file_path)
            if path_obj.exists():
                item = await self._read_code_file(path_obj)
                if item:
                    yield item
                    count += 1

    async def _scan_directory_enhanced(
        self,
        directory: str,
        include_patterns: List[str],
        exclude_patterns: List[str],
        max_size_mb: int,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Enhanced directory scanning with additional metadata collection."""
        dir_path = Path(directory)
        if not dir_path.exists():
            return

        for pattern in include_patterns:
            for file_path in dir_path.rglob(pattern):
                if not file_path.is_file():
                    continue

                # Enhanced exclusion checking
                if self._is_excluded_enhanced(str(file_path), exclude_patterns):
                    continue

                # File size and time checks
                try:
                    stat = file_path.stat()
                    file_size_mb = stat.st_size / (1024 * 1024)
                    if file_size_mb > max_size_mb:
                        self.logger.warning(
                            f"Skipping large file: {file_path} ({file_size_mb:.1f} MB)"
                        )
                        continue

                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    if since and mtime < since:
                        continue
                    if until and mtime > until:
                        continue

                    # Enhanced file info
                    file_info = {
                        "file_path": str(file_path),
                        "size_mb": file_size_mb,
                        "modified_time": mtime,
                        "created_time": datetime.fromtimestamp(stat.st_ctime),
                        "permissions": oct(stat.st_mode)[-3:],
                    }

                    # Add git information if available
                    if self._git_integration_active:
                        git_info = await self._get_git_file_info(str(file_path))
                        file_info.update(git_info)

                    yield file_info

                except OSError as e:
                    self.logger.warning(f"Error accessing file {file_path}: {e}")
                    continue

    def _is_excluded_enhanced(
        self, file_path: str, exclude_patterns: List[str]
    ) -> bool:
        """Enhanced exclusion checking with additional intelligence."""
        if super()._is_excluded(file_path, exclude_patterns):
            return True

        path = Path(file_path)

        # Additional exclusions for enhanced scanning
        enhanced_exclusions = [
            # IDE and editor files
            ".vscode/**",
            ".idea/**",
            "*.swp",
            "*.swo",
            "*~",
            # Build artifacts
            "*.o",
            "*.obj",
            "*.exe",
            "*.dll",
            "*.so",
            "*.dylib",
            # Package managers
            "node_modules/**",
            "bower_components/**",
            "vendor/**",
            # Python specific
            "__pycache__/**",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".tox/**",
            # Cache directories
            ".cache/**",
            ".pytest_cache/**",
            ".mypy_cache/**",
            # Documentation builds
            "_build/**",
            "docs/_build/**",
            "site/**",
            # Large data files
            "*.csv",
            "*.json",
            "*.xml",
            "*.sql",
        ]

        for pattern in enhanced_exclusions:
            if "*" in pattern:
                if path.match(pattern):
                    return True
            else:
                if pattern in str(path):
                    return True

        # Size-based exclusion for very large files
        try:
            if path.stat().st_size > 50 * 1024 * 1024:  # 50MB
                return True
        except OSError:
            pass

        return False

    async def _process_files_parallel(
        self, files: List[Dict[str, Any]], limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Process files in parallel using thread pool."""
        if not self._thread_pool:
            # Fallback to sequential processing
            count = 0
            for file_info in files:
                if limit and count >= limit:
                    break
                item = await self._process_single_file_enhanced(file_info)
                if item:
                    yield item
                    count += 1
            return

        # Process in batches
        batch_size = self.config.source_config.get("max_worker_threads", 4)
        count = 0

        for i in range(0, len(files), batch_size):
            if limit and count >= limit:
                break

            batch = files[i : i + batch_size]
            if limit:
                remaining = limit - count
                batch = batch[:remaining]

            # Submit batch to thread pool
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(
                    self._thread_pool, self._process_file_sync, file_info
                )
                for file_info in batch
            ]

            # Wait for batch completion
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Error in parallel processing: {result}")
                elif result:
                    yield result
                    count += 1

    def _process_file_sync(self, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Synchronous file processing for thread pool execution."""
        try:
            file_path = Path(file_info["file_path"])

            # Check cache first
            if self.config.source_config.get("cache_analysis_results", True):
                cache_key = f"{file_path}:{file_info.get('modified_time', '')}"
                if cache_key in self._analysis_cache:
                    return self._analysis_cache[cache_key]

            # Read and analyze file
            item = self._read_code_file_sync(file_path)
            if not item:
                return None

            # Enhanced analysis
            if self.config.source_config.get("enable_advanced_analysis", True):
                enhanced_data = self._analyze_file_enhanced_sync(item)
                item.update(enhanced_data)

            # Cache result
            if self.config.source_config.get("cache_analysis_results", True):
                cache_key = f"{file_path}:{file_info.get('modified_time', '')}"
                self._analysis_cache[cache_key] = item

            return item

        except Exception as e:
            logger.error(
                f"Error processing file {file_info.get('file_path', 'unknown')}: {e}"
            )
            return None

    def _read_code_file_sync(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Synchronous version of file reading."""
        try:
            # Try different encodings
            encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
            content = None
            encoding_used = None

            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                return None

            # Get file stats
            stat = file_path.stat()
            file_stats = {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "created": datetime.fromtimestamp(stat.st_ctime),
            }

            return {
                "file_path": str(file_path),
                "content": content,
                "encoding": encoding_used,
                "file_stats": file_stats,
                "title": file_path.name,
            }

        except Exception as e:
            logger.error(f"Error reading file: {file_path}: {e}")
            return None

    def _analyze_file_enhanced_sync(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous enhanced file analysis."""
        enhanced_data = {}

        file_path = item["file_path"]
        content = item["content"]
        language = self._detect_language(file_path, content)

        # Extract comprehensive symbols
        symbols = self.extract_symbols(content, file_path, language)
        enhanced_data["detailed_symbols"] = symbols

        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics_sync(content, symbols)
        enhanced_data["quality_metrics"] = quality_metrics

        # Detect architectural patterns
        if self.config.source_config.get("detect_design_patterns", True):
            patterns = self._detect_architectural_patterns_sync(
                content, symbols, language
            )
            enhanced_data["architectural_patterns"] = patterns

        # Calculate complexity metrics
        if self.config.source_config.get("analyze_complexity", True):
            complexity_metrics = self._calculate_complexity_metrics_detailed(
                symbols, content
            )
            enhanced_data["complexity_metrics"] = complexity_metrics

        return enhanced_data

    def _calculate_quality_metrics_sync(
        self, content: str, symbols: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comprehensive quality metrics."""
        lines = content.splitlines()

        metrics = {
            # Basic metrics
            "total_lines": len(lines),
            "code_lines": len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
            ),
            "comment_lines": len(
                [line for line in lines if line.strip().startswith("#")]
            ),
            "blank_lines": len([line for line in lines if not line.strip()]),
            # Complexity metrics
            "cyclomatic_complexity": symbols.get("complexity_metrics", {}).get(
                "total_cyclomatic_complexity", 0
            ),
            "function_count": len(symbols.get("functions", [])),
            "class_count": len(symbols.get("classes", [])),
            # Quality indicators
            "comment_ratio": 0,
            "documentation_coverage": 0,
            "maintainability_index": 0,
        }

        # Calculate ratios
        if metrics["total_lines"] > 0:
            metrics["comment_ratio"] = metrics["comment_lines"] / metrics["total_lines"]

        # Documentation coverage
        documented_items = 0
        total_documentable = 0

        for func in symbols.get("functions", []):
            total_documentable += 1
            if func.get("docstring"):
                documented_items += 1

        for cls in symbols.get("classes", []):
            total_documentable += 1
            if cls.get("docstring"):
                documented_items += 1

        if total_documentable > 0:
            metrics["documentation_coverage"] = documented_items / total_documentable

        # Maintainability index (simplified version)
        # Based on lines of code, complexity, and comment ratio
        if metrics["code_lines"] > 0:
            complexity_penalty = min(
                metrics["cyclomatic_complexity"] / metrics["code_lines"], 1.0
            )
            comment_bonus = metrics["comment_ratio"]
            doc_bonus = metrics["documentation_coverage"]

            metrics["maintainability_index"] = max(
                0, 1.0 - complexity_penalty + (comment_bonus + doc_bonus) / 2
            )

        return metrics

    def _detect_architectural_patterns_sync(
        self, content: str, symbols: Dict[str, Any], language: str
    ) -> List[Dict[str, Any]]:
        """Detect architectural and design patterns in code."""
        patterns = []

        if language == "python":
            patterns.extend(self._detect_python_patterns(content, symbols))
        elif language in ["javascript", "typescript"]:
            patterns.extend(self._detect_js_patterns(content, symbols))

        # Generic patterns that apply to multiple languages
        patterns.extend(self._detect_generic_patterns(content, symbols))

        return patterns

    def _detect_python_patterns(
        self, content: str, symbols: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect Python-specific patterns."""
        patterns = []

        # Singleton pattern
        for cls in symbols.get("classes", []):
            class_name = cls.get("name", "")
            methods = cls.get("methods", [])

            if any(m.get("name") == "__new__" for m in methods):
                if "singleton" in class_name.lower() or "_instance" in content:
                    patterns.append(
                        {
                            "pattern": "Singleton",
                            "confidence": 0.8,
                            "location": cls.get("line_start"),
                            "description": f"Singleton pattern detected in class {class_name}",
                        }
                    )

        # Factory pattern
        for func in symbols.get("functions", []):
            func_name = func.get("name", "")
            if (
                func_name.startswith(("create_", "make_", "build_"))
                or "factory" in func_name.lower()
            ):
                patterns.append(
                    {
                        "pattern": "Factory",
                        "confidence": 0.6,
                        "location": func.get("line_start"),
                        "description": f"Factory pattern detected in function {func_name}",
                    }
                )

        # Observer pattern
        if any(
            "observer" in func.get("name", "").lower()
            for func in symbols.get("functions", [])
        ):
            patterns.append(
                {
                    "pattern": "Observer",
                    "confidence": 0.7,
                    "location": 0,
                    "description": "Observer pattern detected",
                }
            )

        # Decorator pattern (Python decorators)
        decorators = symbols.get("decorators", [])
        if decorators:
            patterns.append(
                {
                    "pattern": "Decorator",
                    "confidence": 0.9,
                    "location": 0,
                    "description": f"Decorator pattern detected ({len(decorators)} decorators found)",
                }
            )

        return patterns

    def _detect_js_patterns(
        self, content: str, symbols: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect JavaScript/TypeScript patterns."""
        patterns = []

        # Module pattern
        if "module.exports" in content or "export" in content:
            patterns.append(
                {
                    "pattern": "Module",
                    "confidence": 0.9,
                    "location": 0,
                    "description": "Module pattern detected",
                }
            )

        # Promise/Async patterns
        if "async" in content or "Promise" in content:
            patterns.append(
                {
                    "pattern": "Promise/Async",
                    "confidence": 0.8,
                    "location": 0,
                    "description": "Asynchronous programming pattern detected",
                }
            )

        return patterns

    def _detect_generic_patterns(
        self, content: str, symbols: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect language-agnostic patterns."""
        patterns = []

        # MVC pattern indicators
        mvc_indicators = ["controller", "model", "view"]
        if any(indicator in content.lower() for indicator in mvc_indicators):
            patterns.append(
                {
                    "pattern": "MVC",
                    "confidence": 0.6,
                    "location": 0,
                    "description": "MVC architecture pattern indicators found",
                }
            )

        # Strategy pattern
        if len(symbols.get("classes", [])) > 1:
            class_names = [cls.get("name", "") for cls in symbols.get("classes", [])]
            if any("strategy" in name.lower() for name in class_names):
                patterns.append(
                    {
                        "pattern": "Strategy",
                        "confidence": 0.7,
                        "location": 0,
                        "description": "Strategy pattern detected",
                    }
                )

        return patterns

    async def _process_single_file_enhanced(
        self, file_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process a single file with enhanced analysis."""
        try:
            file_path = Path(file_info["file_path"])

            # Read file
            item = await self._read_code_file(file_path)
            if not item:
                return None

            # Enhanced analysis
            if self.config.source_config.get("enable_advanced_analysis", True):
                loop = asyncio.get_event_loop()
                enhanced_data = await loop.run_in_executor(
                    self._thread_pool if self._thread_pool else None,
                    self._analyze_file_enhanced_sync,
                    item,
                )
                item.update(enhanced_data)

            return item

        except Exception as e:
            self.logger.error(
                f"Error processing file {file_info.get('file_path', 'unknown')}: {e}"
            )
            return None

    async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Enhanced item transformation with additional metadata."""
        # Use parent transformation as base
        item = await super().transform_item(raw_item)

        # Add enhanced metadata
        if "quality_metrics" in raw_item:
            if item.metrics:
                item.metrics.update(raw_item["quality_metrics"])
            else:
                item.metrics = raw_item["quality_metrics"]

        if "architectural_patterns" in raw_item:
            if item.metrics:
                item.metrics["architectural_patterns"] = raw_item[
                    "architectural_patterns"
                ]
            else:
                item.metrics = {
                    "architectural_patterns": raw_item["architectural_patterns"]
                }

        # Enhanced tagging
        if raw_item.get("quality_metrics"):
            quality = raw_item["quality_metrics"]

            # Add quality-based tags
            if quality.get("maintainability_index", 0) < 0.3:
                item.tags = (item.tags or []) + ["low_maintainability"]

            if quality.get("cyclomatic_complexity", 0) > self.config.source_config.get(
                "complexity_threshold", 10
            ):
                item.tags = (item.tags or []) + ["high_complexity"]

            if quality.get("documentation_coverage", 0) < self.config.source_config.get(
                "documentation_threshold", 0.7
            ):
                item.tags = (item.tags or []) + ["needs_documentation"]

        return item

    # ============================================
    # FILE WATCHING AND REAL-TIME MONITORING
    # ============================================

    async def start_file_watcher(self) -> None:
        """Start file system watcher for real-time updates."""
        if self._file_watcher_active:
            return

        self._file_watcher_active = True
        scan_dirs = self.config.source_config.get("scan_directories", ["."])

        try:
            # Try to use inotify for efficient file watching
            import asyncinotify

            async def watch_directories():
                async with asyncinotify.Inotify() as inotify:
                    watch_masks = (
                        asyncinotify.Mask.MODIFY
                        | asyncinotify.Mask.CREATE
                        | asyncinotify.Mask.DELETE
                        | asyncinotify.Mask.MOVED_TO
                        | asyncinotify.Mask.MOVED_FROM
                    )

                    for scan_dir in scan_dirs:
                        dir_path = Path(scan_dir)
                        if dir_path.exists():
                            inotify.add_watch(dir_path, watch_masks, recursive=True)

                    self.logger.info(
                        f"Started file watcher for {len(scan_dirs)} directories"
                    )

                    async for event in inotify:
                        if not self._file_watcher_active:
                            break

                        await self._handle_file_change_event(event)

            # Start watcher task
            asyncio.create_task(watch_directories())

        except ImportError:
            # Fallback to polling-based watching
            self.logger.info(
                "asyncinotify not available, using polling-based file watching"
            )
            asyncio.create_task(self._polling_file_watcher())

    async def _polling_file_watcher(self) -> None:
        """Fallback polling-based file watcher."""
        last_check_times = {}

        while self._file_watcher_active:
            try:
                changed_files = await self._get_changed_files_since_last_check(
                    last_check_times
                )

                for file_path in changed_files:
                    await self._handle_file_change(file_path)
                    last_check_times[file_path] = time.time()

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                self.logger.error(f"Error in file watcher: {e}")
                await asyncio.sleep(10)  # Wait longer on error

    async def _handle_file_change_event(self, event) -> None:
        """Handle inotify file change event."""
        try:
            file_path = str(event.path)

            # Filter out irrelevant events
            if not self._should_process_file_change(file_path):
                return

            self.logger.debug(f"File change detected: {file_path} ({event.mask.name})")

            await self._handle_file_change(file_path)

        except Exception as e:
            self.logger.error(f"Error handling file change event: {e}")

    async def _handle_file_change(self, file_path: str) -> None:
        """Handle a file change event with enhanced processing."""
        try:
            path = Path(file_path)

            # Check if file matches our patterns
            if not self._should_process_file_change(file_path):
                return

            self.logger.info(f"Processing file change: {file_path}")

            # Invalidate caches
            self.invalidate_cache_for_files([file_path])

            # Update dependency graph if the file was deleted
            if not path.exists():
                self._remove_from_dependency_graph(file_path)
                return

            # Immediate re-analysis if enabled
            if self.config.source_config.get("immediate_reanalysis", False):
                await self._analyze_single_file_immediately(path)

            # Update quality metrics
            self._quality_metrics["total_files_analyzed"] += 1

        except Exception as e:
            self.logger.error(f"Error handling file change for {file_path}: {e}")

    def _should_process_file_change(self, file_path: str) -> bool:
        """Determine if a file change should be processed."""
        path = Path(file_path)

        # Check include patterns
        include_patterns = self.config.source_config.get("include_patterns", ["*"])
        if not any(path.match(pattern) for pattern in include_patterns):
            return False

        # Check exclude patterns
        exclude_patterns = self.config.source_config.get("exclude_patterns", [])
        if self._is_excluded_enhanced(file_path, exclude_patterns):
            return False

        return True

    async def _analyze_single_file_immediately(self, file_path: Path) -> None:
        """Immediately analyze a single file that changed."""
        try:
            # Read and analyze file
            item = await self._read_code_file(file_path)
            if not item:
                return

            # Enhanced analysis
            if self.config.source_config.get("enable_advanced_analysis", True):
                loop = asyncio.get_event_loop()
                enhanced_data = await loop.run_in_executor(
                    self._thread_pool, self._analyze_file_enhanced_sync, item
                )
                item.update(enhanced_data)

            # Update symbol index
            if "detailed_symbols" in item:
                await self._update_symbol_index(
                    str(file_path), item["detailed_symbols"]
                )

            self.logger.info(f"Completed immediate analysis of {file_path}")

        except Exception as e:
            self.logger.error(f"Error in immediate analysis of {file_path}: {e}")

    # ============================================
    # GIT INTEGRATION
    # ============================================

    async def _initialize_git_integration(self) -> None:
        """Initialize git integration for enhanced change tracking."""
        try:
            # Check if we're in a git repository
            result = await asyncio.create_subprocess_exec(
                "git",
                "rev-parse",
                "--git-dir",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                self._git_integration_active = True
                self.logger.info("Git integration enabled")
            else:
                self.logger.info("Not in a git repository, git integration disabled")
        except Exception as e:
            self.logger.warning(f"Failed to initialize git integration: {e}")

    async def _get_git_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get git information for a specific file."""
        if not self._git_integration_active:
            return {}

        git_info = {}

        try:
            # Get last commit info for file
            cmd = ["git", "log", "-1", "--format=%h|%an|%at|%s", "--", file_path]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and stdout:
                commit_data = stdout.decode().strip()
                if commit_data:
                    parts = commit_data.split("|", 3)
                    if len(parts) >= 4:
                        git_info.update(
                            {
                                "last_commit_hash": parts[0],
                                "last_commit_author": parts[1],
                                "last_commit_timestamp": int(parts[2]),
                                "last_commit_message": parts[3],
                            }
                        )

            # Get file status
            status_cmd = ["git", "status", "--porcelain", file_path]
            status_process = await asyncio.create_subprocess_exec(
                *status_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            status_stdout, _ = await status_process.communicate()

            if status_process.returncode == 0:
                status_line = status_stdout.decode().strip()
                if status_line:
                    git_info["git_status"] = status_line[
                        :2
                    ]  # First two characters indicate status
                else:
                    git_info["git_status"] = "  "  # Clean/committed

        except Exception as e:
            self.logger.debug(f"Error getting git info for {file_path}: {e}")

        return git_info

    async def get_recent_git_changes(
        self, since_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get files changed in git within the specified time period."""
        if not self._git_integration_active:
            return []

        changes = []

        try:
            cmd = [
                "git",
                "log",
                f'--since="{since_hours} hours ago"',
                "--name-status",
                "--format=%h|%an|%at|%s",
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                lines = stdout.decode().strip().split("\n")
                current_commit = None

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Check if it's a commit line
                    if "|" in line and not line.startswith(("A", "M", "D")):
                        parts = line.split("|", 3)
                        if len(parts) >= 4:
                            current_commit = {
                                "hash": parts[0],
                                "author": parts[1],
                                "timestamp": int(parts[2]),
                                "message": parts[3],
                                "files": [],
                            }
                            changes.append(current_commit)

                    # Check if it's a file status line
                    elif line.startswith(("A", "M", "D")) and current_commit:
                        parts = line.split("\t", 1)
                        if len(parts) == 2:
                            status = parts[0].strip()
                            file_path = parts[1].strip()

                            current_commit["files"].append(
                                {"status": status, "path": file_path}
                            )

        except Exception as e:
            self.logger.warning(f"Failed to get recent git changes: {e}")

        return changes

    # ============================================
    # SYMBOL INDEXING AND DEPENDENCY TRACKING
    # ============================================

    async def _initialize_symbol_index(self) -> None:
        """Initialize the enhanced symbol index."""
        self._symbol_index = {}
        self._dependency_graph = {}
        self.logger.info("Enhanced symbol index initialized")

    async def _update_symbol_index(
        self, file_path: str, symbols: Dict[str, Any]
    ) -> None:
        """Update the symbol index with comprehensive symbol information."""
        if not symbols:
            return

        # Clear existing symbols for this file
        self._remove_file_from_symbol_index(file_path)

        # Index functions with detailed information
        for func in symbols.get("functions", []):
            func_name = func.get("name")
            if func_name:
                if func_name not in self._symbol_index:
                    self._symbol_index[func_name] = []

                symbol_entry = {
                    "file_path": file_path,
                    "type": "function",
                    "line_start": func.get("line_start"),
                    "line_end": func.get("line_end"),
                    "signature": func.get("signature"),
                    "complexity": func.get("complexity_score", 1),
                    "parameters": func.get("parameters", []),
                    "calls": func.get("calls", []),
                    "is_async": func.get("is_async", False),
                    "docstring": func.get("docstring"),
                    "decorators": func.get("decorators", []),
                }
                self._symbol_index[func_name].append(symbol_entry)

        # Index classes with method information
        for cls in symbols.get("classes", []):
            cls_name = cls.get("name")
            if cls_name:
                if cls_name not in self._symbol_index:
                    self._symbol_index[cls_name] = []

                symbol_entry = {
                    "file_path": file_path,
                    "type": "class",
                    "line_start": cls.get("line_start"),
                    "line_end": cls.get("line_end"),
                    "base_classes": cls.get("base_classes", []),
                    "methods": [m.get("name") for m in cls.get("methods", [])],
                    "method_count": len(cls.get("methods", [])),
                    "docstring": cls.get("docstring"),
                    "decorators": cls.get("decorators", []),
                }
                self._symbol_index[cls_name].append(symbol_entry)

        # Index variables and constants
        for var in symbols.get("variables", []):
            var_name = var.get("name")
            if var_name:
                if var_name not in self._symbol_index:
                    self._symbol_index[var_name] = []

                self._symbol_index[var_name].append(
                    {
                        "file_path": file_path,
                        "type": "variable",
                        "line": var.get("line"),
                        "type_annotation": var.get("type_annotation"),
                    }
                )

        for const in symbols.get("constants", []):
            const_name = const.get("name")
            if const_name:
                if const_name not in self._symbol_index:
                    self._symbol_index[const_name] = []

                self._symbol_index[const_name].append(
                    {
                        "file_path": file_path,
                        "type": "constant",
                        "line": const.get("line"),
                        "type_annotation": const.get("type_annotation"),
                    }
                )

        # Update dependency graph
        self._update_dependency_graph(file_path, symbols)

    def _remove_file_from_symbol_index(self, file_path: str) -> None:
        """Remove all symbols from a file from the index."""
        symbols_to_remove = []

        for symbol_name, entries in self._symbol_index.items():
            # Filter out entries from this file
            self._symbol_index[symbol_name] = [
                entry for entry in entries if entry.get("file_path") != file_path
            ]

            # Mark empty symbol entries for removal
            if not self._symbol_index[symbol_name]:
                symbols_to_remove.append(symbol_name)

        # Remove empty symbol entries
        for symbol_name in symbols_to_remove:
            del self._symbol_index[symbol_name]

    def _update_dependency_graph(self, file_path: str, symbols: Dict[str, Any]) -> None:
        """Update the dependency graph for cross-file relationships."""
        dependencies = set()

        # Add import dependencies
        for imp in symbols.get("imports", []):
            module_name = imp.get("module", "")
            if module_name:
                dependencies.add(module_name)

        # Add function call dependencies (cross-file)
        for func in symbols.get("functions", []):
            for call in func.get("calls", []):
                # Check if call references a symbol in our index
                if call in self._symbol_index:
                    for symbol_entry in self._symbol_index[call]:
                        dep_file = symbol_entry.get("file_path")
                        if dep_file and dep_file != file_path:
                            dependencies.add(dep_file)

        self._dependency_graph[file_path] = dependencies

    def _remove_from_dependency_graph(self, file_path: str) -> None:
        """Remove a file from the dependency graph."""
        # Remove the file's dependencies
        if file_path in self._dependency_graph:
            del self._dependency_graph[file_path]

        # Remove references to this file from other dependencies
        for deps in self._dependency_graph.values():
            deps.discard(file_path)

    # ============================================
    # METRICS AND REPORTING
    # ============================================

    async def _update_quality_metrics(self) -> None:
        """Update quality metrics tracking."""
        # This could be expanded to include more sophisticated metrics
        self.logger.debug("Quality metrics updated", metrics=self._quality_metrics)

    async def get_comprehensive_repository_report(self) -> Dict[str, Any]:
        """Generate a comprehensive repository analysis report."""
        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "basic_statistics": await self.get_repository_statistics(),
            "quality_metrics": self._quality_metrics.copy(),
            "symbol_index_statistics": {
                "total_symbols": len(self._symbol_index),
                "functions": len(
                    [
                        name
                        for name, entries in self._symbol_index.items()
                        if any(e.get("type") == "function" for e in entries)
                    ]
                ),
                "classes": len(
                    [
                        name
                        for name, entries in self._symbol_index.items()
                        if any(e.get("type") == "class" for e in entries)
                    ]
                ),
                "variables": len(
                    [
                        name
                        for name, entries in self._symbol_index.items()
                        if any(e.get("type") == "variable" for e in entries)
                    ]
                ),
            },
            "dependency_graph_statistics": {
                "total_files": len(self._dependency_graph),
                "total_dependencies": sum(
                    len(deps) for deps in self._dependency_graph.values()
                ),
                "avg_dependencies_per_file": sum(
                    len(deps) for deps in self._dependency_graph.values()
                )
                / len(self._dependency_graph)
                if self._dependency_graph
                else 0,
            },
            "integration_status": {
                "git_integration": self._git_integration_active,
                "file_watcher": self._file_watcher_active,
                "incremental_enabled": self._incremental_enabled,
                "parallel_processing": self._thread_pool is not None,
            },
        }

        # Add git-specific information if available
        if self._git_integration_active:
            recent_changes = await self.get_recent_git_changes(
                since_hours=168
            )  # Last week
            report["git_activity"] = {
                "commits_last_week": len(recent_changes),
                "active_contributors": len(
                    set(change.get("author", "") for change in recent_changes)
                ),
                "most_active_files": self._get_most_changed_files(recent_changes),
            }

        return report

    def _get_most_changed_files(
        self, git_changes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get the most frequently changed files from git history."""
        file_change_counts = {}

        for change in git_changes:
            for file_info in change.get("files", []):
                file_path = file_info.get("path", "")
                if file_path:
                    file_change_counts[file_path] = (
                        file_change_counts.get(file_path, 0) + 1
                    )

        # Sort by change count and return top 10
        most_changed = sorted(
            file_change_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return [
            {"file_path": path, "change_count": count} for path, count in most_changed
        ]

    async def cleanup(self) -> None:
        """Enhanced cleanup with thread pool management."""
        self.logger.info("Cleaning up enhanced code adapter")

        # Stop file watcher
        if self._file_watcher_active:
            self._file_watcher_active = False
            self.logger.info("Stopped file watcher")

        # Shutdown thread pool
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            self.logger.info("Shutdown thread pool")

        # Clear all caches and indexes
        self._file_checksums.clear()
        self._processed_files.clear()
        self._symbol_index.clear()
        self._dependency_graph.clear()
        self._proj_intel_cache.clear()
        self._analysis_cache.clear()

        self.logger.info("Enhanced code adapter cleanup completed")

    # Helper methods for advanced analysis

    def get_cross_file_references(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Get all cross-file references to a symbol."""
        references = []

        if symbol_name in self._symbol_index:
            symbol_files = {
                entry.get("file_path") for entry in self._symbol_index[symbol_name]
            }

            # Look for references in other files
            for file_path, deps in self._dependency_graph.items():
                if file_path not in symbol_files:
                    # Check if this file depends on files containing the symbol
                    if any(dep_file in symbol_files for dep_file in deps):
                        references.append(
                            {
                                "referencing_file": file_path,
                                "symbol_locations": [
                                    entry
                                    for entry in self._symbol_index[symbol_name]
                                    if entry.get("file_path") in deps
                                ],
                            }
                        )

        return references

    def analyze_code_hotspots(self) -> List[Dict[str, Any]]:
        """Identify code hotspots based on complexity and change frequency."""
        hotspots = []

        # Combine symbol complexity with file change frequency (if git available)
        for symbol_name, entries in self._symbol_index.items():
            for entry in entries:
                if entry.get("type") == "function":
                    complexity = entry.get("complexity", 1)
                    if complexity > self.config.source_config.get(
                        "complexity_threshold", 10
                    ):
                        hotspot = {
                            "symbol": symbol_name,
                            "file_path": entry.get("file_path"),
                            "complexity": complexity,
                            "type": "high_complexity",
                            "line": entry.get("line_start"),
                        }
                        hotspots.append(hotspot)

        return sorted(hotspots, key=lambda x: x["complexity"], reverse=True)
