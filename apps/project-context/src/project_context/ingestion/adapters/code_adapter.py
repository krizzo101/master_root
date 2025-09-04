"""Code source adapter for file system and IDE integration."""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Union

import structlog

from ...models.common import ContextItem
from ..base_adapter import AdapterConfig, BaseAdapter, BatchMode
from ..transformers import DataTransformer

logger = structlog.get_logger(__name__)


class CodeAdapter(BaseAdapter):
    """Adapter for ingesting code files and IDE data.

    Supports:
    - File system scanning
    - IDE change tracking
    - Code analysis and metadata extraction
    - Function/class/module extraction
    """

    @classmethod
    def default_config(cls) -> AdapterConfig:
        """Get default configuration for code adapter."""
        return AdapterConfig(
            adapter_id="code",
            source_type="code",
            batch_mode=BatchMode.BATCH,
            batch_size=200,
            generate_embeddings=True,
            generate_summaries=True,
            extract_relationships=True,
            source_config={
                "scan_directories": ["."],
                "include_patterns": [
                    "*.py",
                    "*.js",
                    "*.ts",
                    "*.jsx",
                    "*.tsx",
                    "*.java",
                    "*.cpp",
                    "*.c",
                    "*.h",
                    "*.hpp",
                    "*.rs",
                    "*.go",
                    "*.rb",
                    "*.php",
                    "*.swift",
                    "*.kt",
                    "*.scala",
                    "*.sql",
                    "*.html",
                    "*.css",
                    "*.json",
                    "*.yaml",
                    "*.yml",
                    "*.xml",
                    "*.md",
                ],
                "exclude_patterns": [
                    "node_modules/**",
                    ".git/**",
                    "__pycache__/**",
                    "*.pyc",
                    "*.pyo",
                    "*.pyd",
                    ".pytest_cache/**",
                    "build/**",
                    "dist/**",
                    ".venv/**",
                    "venv/**",
                    ".env",
                    "*.log",
                    "*.tmp",
                    "*.temp",
                ],
                "max_file_size_mb": 10,
                "extract_functions": True,
                "extract_classes": True,
                "extract_imports": True,
                "extract_comments": True,
                "track_changes": True,
                "use_git_tracking": True,
                "enable_proj_intel": True,
                "proj_intel_paths": [".proj-intel"],
                "ingest_file_elements": True,
                "ingest_project_analysis": True,
                "ingest_symbol_index": True,
                "proj_intel_max_age_days": 7,
            },
        )

    def __init__(self, config: AdapterConfig):
        """Initialize code adapter."""
        super().__init__(config)
        self.transformer = DataTransformer()
        self._file_checksums: Dict[str, str] = {}
        self._processed_files: Set[str] = set()
        self._language_parsers: Dict[str, callable] = {}
        self._proj_intel_cache: Dict[str, Any] = {}
        self._proj_intel_manifest: Optional[Dict[str, Any]] = None
        self._setup_parsers()

    async def initialize(self) -> None:
        """Initialize code adapter resources."""
        self.logger.info("Initializing code adapter")

        # Validate scan directories
        scan_dirs = self.config.source_config.get("scan_directories", ["."])
        for directory in scan_dirs:
            if not Path(directory).exists():
                self.logger.warning(f"Scan directory does not exist: {directory}")

        # Initialize file tracking
        self._file_checksums = {}
        self._processed_files = set()
        self._proj_intel_cache = {}

        # Initialize .proj-intel data if enabled
        if self.config.source_config.get("enable_proj_intel", True):
            await self._initialize_proj_intel()

        self.logger.info("Code adapter initialized")

    async def fetch_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch code files and .proj-intel data."""
        count = 0

        # First, yield .proj-intel data if enabled
        if self.config.source_config.get("enable_proj_intel", True):
            async for intel_item in self._fetch_proj_intel_items(since, until):
                if limit and count >= limit:
                    return
                yield intel_item
                count += 1

        # Then yield regular file system items
        scan_dirs = self.config.source_config.get("scan_directories", ["."])
        include_patterns = self.config.source_config.get("include_patterns", ["*"])
        exclude_patterns = self.config.source_config.get("exclude_patterns", [])
        max_size_mb = self.config.source_config.get("max_file_size_mb", 10)

        for directory in scan_dirs:
            async for item in self._scan_directory(
                directory, include_patterns, exclude_patterns, max_size_mb, since, until
            ):
                if limit and count >= limit:
                    return

                yield item
                count += 1

    async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform raw code item or .proj-intel data into ContextItem."""
        file_path = raw_item["file_path"]

        # Check if this is .proj-intel data
        intel_data_type = raw_item.get("intel_data_type")
        if intel_data_type:
            return await self._transform_intel_item(raw_item)

        # Handle regular code files
        # Create base context item
        item = self.transformer.create_base_context_item(
            source_type="code", source_id=file_path, raw_data=raw_item
        )

        # Code-specific fields
        item.title = raw_item.get("title") or Path(file_path).name
        item.content = raw_item.get("content", "")
        item.file_path = file_path

        # Extract language and file metadata
        file_stats = raw_item.get("file_stats", {})
        language = self._detect_language(file_path, item.content)

        code_metadata = {
            "language": language,
            "file_size": file_stats.get("size", 0),
            "line_count": len(item.content.splitlines()) if item.content else 0,
            "encoding": raw_item.get("encoding", "utf-8"),
            "extension": Path(file_path).suffix.lower(),
        }

        # Extract code elements if enabled - use enhanced symbol extraction
        if self.config.source_config.get("extract_functions", True):
            code_metadata["functions"] = self._extract_functions(item.content, language)

        if self.config.source_config.get("extract_classes", True):
            code_metadata["classes"] = self._extract_classes(item.content, language)

        if self.config.source_config.get("extract_imports", True):
            code_metadata["imports"] = self._extract_imports(item.content, language)

        if self.config.source_config.get("extract_comments", True):
            code_metadata["comments"] = self._extract_comments(item.content, language)

        # Enhanced symbol extraction for detailed analysis
        if self.config.source_config.get("enable_advanced_analysis", True):
            try:
                detailed_symbols = self.extract_symbols(
                    item.content, file_path, language
                )
                code_metadata["detailed_symbols"] = detailed_symbols

                # Merge complexity metrics
                code_metadata.update(detailed_symbols.get("complexity_metrics", {}))

                # Add dependency information
                if detailed_symbols.get("imports"):
                    code_metadata["dependencies"] = [
                        imp.get("module", imp.get("name", ""))
                        for imp in detailed_symbols["imports"]
                        if imp.get("module") or imp.get("name")
                    ]
            except Exception as e:
                self.logger.warning(
                    f"Advanced symbol analysis failed for {file_path}: {e}"
                )

        if item.metrics:
            item.metrics.update(code_metadata)
        else:
            item.metrics = code_metadata

        # Set entity type based on content
        item.entity_type = self._determine_entity_type(
            file_path, item.content, language
        )

        # Add language-based tags
        tags = [language] if language else []
        if code_metadata.get("functions"):
            tags.append("has_functions")
        if code_metadata.get("classes"):
            tags.append("has_classes")

        item.tags = tags

        # Apply transformations
        item = await self.transformer.transform_item(item)

        return item

    async def _transform_intel_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform .proj-intel data into ContextItem."""
        intel_data_type = raw_item["intel_data_type"]
        file_path = raw_item["file_path"]

        # Create base context item with intelligence source type
        item = self.transformer.create_base_context_item(
            source_type="code_intelligence",
            source_id=f"{intel_data_type}:{file_path}",
            raw_data=raw_item,
        )

        # Set basic fields
        item.title = raw_item.get("title", f"Code Intelligence: {intel_data_type}")
        item.content = raw_item.get("content", "")
        item.file_path = file_path

        # Create intelligence-specific metadata
        intel_metadata = {
            "intel_data_type": intel_data_type,
            "generated_at": raw_item.get("generated_at"),
            "source": "proj_intel",
        }

        # Add type-specific metadata
        if intel_data_type == "file_element":
            intel_metadata.update(
                {
                    "line_count": raw_item.get("line_count", 0),
                    "content_hash": raw_item.get("content_hash"),
                    "functions": raw_item.get("functions", []),
                    "classes": raw_item.get("classes", []),
                    "imports": raw_item.get("imports", []),
                    "code_analysis": raw_item.get("code_analysis", {}),
                }
            )
            # Set entity type based on code analysis
            if raw_item.get("classes"):
                item.entity_type = "code_file_with_classes"
            elif raw_item.get("functions"):
                item.entity_type = "code_file_with_functions"
            else:
                item.entity_type = "code_file_analyzed"

        elif intel_data_type == "project_analysis":
            intel_metadata.update(
                {
                    "collector": raw_item.get("collector"),
                    "analysis_type": raw_item.get("analysis_type"),
                    "schema_version": raw_item.get("schema_version"),
                    "timestamp": raw_item.get("timestamp"),
                    "analysis_data": raw_item.get("analysis_data", {}),
                }
            )
            item.entity_type = f"analysis_{raw_item.get('analysis_type', 'unknown')}"

        elif intel_data_type == "symbol":
            intel_metadata.update(
                {
                    "symbol_type": raw_item.get("symbol_type"),
                    "symbol_name": raw_item.get("symbol_name"),
                    "symbol_data": raw_item.get("symbol_data", {}),
                }
            )
            item.entity_type = f"symbol_{raw_item.get('symbol_type', 'unknown')}"

        item.metrics = intel_metadata

        # Create intelligent tags
        tags = [intel_data_type, "code_intelligence", "proj_intel"]

        if intel_data_type == "file_element":
            if raw_item.get("functions"):
                tags.append("has_functions")
            if raw_item.get("classes"):
                tags.append("has_classes")
            if raw_item.get("imports"):
                tags.append("has_imports")

            # Detect language from file path
            if not file_path.startswith("<"):
                language = self._detect_language(file_path, item.content)
                if language and language != "unknown":
                    tags.append(language)

        elif intel_data_type == "project_analysis":
            collector = raw_item.get("collector", "")
            if collector:
                tags.append(f"collector_{collector.lower()}")

        elif intel_data_type == "symbol":
            symbol_type = raw_item.get("symbol_type", "")
            if symbol_type:
                tags.append(f"symbol_{symbol_type}")

        item.tags = tags

        # Apply transformations
        item = await self.transformer.transform_item(item)

        return item

    async def detect_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships with other code files and intelligence data."""
        relationships = []

        if not item.metrics:
            return relationships

        # Use enhanced relationship detection if advanced analysis is enabled
        if self.config.source_config.get("enable_advanced_analysis", False):
            try:
                enhanced_relationships = self.detect_enhanced_relationships(
                    item, context_window
                )
                relationships.extend(enhanced_relationships)
                return relationships
            except Exception as e:
                self.logger.warning(
                    f"Enhanced relationship detection failed, falling back to basic: {e}"
                )

        # Handle different relationship types based on source type (original implementation)
        if item.source_type == "code_intelligence":
            relationships.extend(
                await self._detect_intelligence_relationships(item, context_window)
            )
        else:
            relationships.extend(
                await self._detect_code_relationships(item, context_window)
            )

        return relationships

    async def _detect_code_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships for regular code files."""
        relationships = []

        item_imports = item.metrics.get("imports", [])
        item_path = item.file_path

        for context_item in context_window:
            if (
                context_item.source_type not in ["code", "code_intelligence"]
                or not context_item.metrics
            ):
                continue

            context_path = context_item.file_path
            if context_path == item_path:
                continue

            # Import relationships
            for import_stmt in item_imports:
                if self._matches_import(import_stmt, context_path):
                    relationships.append(("imports", context_item.id, 0.9))

            # Enhanced relationships with intelligence data
            if context_item.source_type == "code_intelligence":
                # Check if intelligence data is about this file
                if context_item.metrics.get("intel_data_type") == "file_element":
                    if context_path == item_path or context_path.endswith(item_path):
                        relationships.append(("analyzed_by", context_item.id, 0.95))

            # Directory relationships
            if item_path and context_path and not context_path.startswith("<"):
                if Path(item_path).parent == Path(context_path).parent:
                    relationships.append(("same_directory", context_item.id, 0.3))

                # Check if one file is in a subdirectory of the other
                if str(Path(item_path).parent) in str(context_path):
                    relationships.append(("parent_directory", context_item.id, 0.4))
                elif str(Path(context_path).parent) in str(item_path):
                    relationships.append(("child_directory", context_item.id, 0.4))

            # Language relationships
            item_lang = item.metrics.get("language")
            context_lang = context_item.metrics.get("language")
            if item_lang and context_lang and item_lang == context_lang:
                relationships.append(("same_language", context_item.id, 0.2))

        return relationships

    async def _detect_intelligence_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships for code intelligence data."""
        relationships = []

        intel_data_type = item.metrics.get("intel_data_type")
        item_path = item.file_path

        for context_item in context_window:
            if not context_item.metrics:
                continue

            context_path = context_item.file_path
            if context_path == item_path:
                continue

            # Relationships based on intelligence data type
            if intel_data_type == "file_element":
                # Link to actual source files
                if context_item.source_type == "code":
                    if context_path == item_path or item_path.endswith(context_path):
                        relationships.append(("analyzes", context_item.id, 0.95))

                # Link to related file elements
                elif (
                    context_item.source_type == "code_intelligence"
                    and context_item.metrics.get("intel_data_type") == "file_element"
                ):
                    # Check for import relationships via .proj-intel data
                    item_imports = item.metrics.get("imports", [])
                    for import_data in item_imports:
                        if isinstance(import_data, dict):
                            import_module = import_data.get("module", "")
                        else:
                            import_module = str(import_data)

                        if (
                            import_module
                            and context_path
                            and import_module in context_path
                        ):
                            relationships.append(
                                ("imports_analysis", context_item.id, 0.8)
                            )

            elif intel_data_type == "project_analysis":
                # Link project analysis to relevant code files
                if context_item.source_type == "code":
                    analysis_data = item.metrics.get("analysis_data", {})
                    # Check if the analysis mentions this file
                    if self._analysis_mentions_file(analysis_data, context_path):
                        relationships.append(("analyzes_project", context_item.id, 0.7))

            elif intel_data_type == "symbol":
                # Link symbols to files that contain them
                if context_item.source_type == "code":
                    symbol_name = item.metrics.get("symbol_name", "")
                    if (
                        symbol_name
                        and context_item.content
                        and symbol_name in context_item.content
                    ):
                        relationships.append(
                            ("symbol_defined_in", context_item.id, 0.85)
                        )

            # Same project relationships
            if context_item.source_type == "code_intelligence" and item.metrics.get(
                "generated_at"
            ) == context_item.metrics.get("generated_at"):
                relationships.append(("same_analysis_run", context_item.id, 0.4))

        return relationships

    def _analysis_mentions_file(
        self, analysis_data: Dict[str, Any], file_path: str
    ) -> bool:
        """Check if analysis data mentions a specific file."""
        if not analysis_data or not file_path:
            return False

        # Convert analysis data to string for search
        analysis_str = json.dumps(analysis_data).lower()
        file_name = Path(file_path).name.lower()
        file_stem = Path(file_path).stem.lower()

        # Check for file name or stem in analysis
        return file_name in analysis_str or file_stem in analysis_str

    async def cleanup(self) -> None:
        """Clean up code adapter resources."""
        self.logger.info("Cleaning up code adapter")
        self._file_checksums.clear()
        self._processed_files.clear()

    # Private methods

    async def _initialize_proj_intel(self) -> None:
        """Initialize .proj-intel data sources."""
        proj_intel_paths = self.config.source_config.get(
            "proj_intel_paths", [".proj-intel"]
        )

        for intel_path in proj_intel_paths:
            intel_dir = Path(intel_path)
            if not intel_dir.is_absolute():
                # Make relative to scan directories
                scan_dirs = self.config.source_config.get("scan_directories", ["."])
                for scan_dir in scan_dirs:
                    full_path = Path(scan_dir) / intel_dir
                    if full_path.exists():
                        intel_dir = full_path
                        break

            if intel_dir.exists():
                try:
                    await self._load_proj_intel_manifest(intel_dir)
                    self.logger.info("Loaded .proj-intel data", path=str(intel_dir))
                except Exception as e:
                    self.logger.error(
                        "Failed to load .proj-intel data",
                        path=str(intel_dir),
                        error=str(e),
                    )
            else:
                self.logger.warning(
                    "Project intel directory not found", path=str(intel_dir)
                )

    async def _load_proj_intel_manifest(self, intel_dir: Path) -> None:
        """Load .proj-intel manifest and cache key files."""
        manifest_path = intel_dir / "proj_intel_manifest.json"
        if not manifest_path.exists():
            self.logger.warning("No manifest found", path=str(manifest_path))
            return

        try:
            with open(manifest_path, "r") as f:
                self._proj_intel_manifest = json.load(f)

            # Cache frequently used files
            await self._cache_proj_intel_files(intel_dir)

        except Exception as e:
            self.logger.error(
                "Failed to load manifest", path=str(manifest_path), error=str(e)
            )

    async def _cache_proj_intel_files(self, intel_dir: Path) -> None:
        """Cache important .proj-intel files for faster access."""
        if not self._proj_intel_manifest:
            return

        # Cache symbol index if it exists
        symbol_index_path = intel_dir / "symbol_index.json"
        if symbol_index_path.exists():
            try:
                with open(symbol_index_path, "r") as f:
                    self._proj_intel_cache["symbol_index"] = json.load(f)
                self.logger.debug("Cached symbol index")
            except Exception as e:
                self.logger.warning("Failed to cache symbol index", error=str(e))

        # Cache project analysis index
        analysis_index_path = intel_dir / "project_analysis.index.json"
        if analysis_index_path.exists():
            try:
                with open(analysis_index_path, "r") as f:
                    self._proj_intel_cache["analysis_index"] = json.load(f)
                self.logger.debug("Cached analysis index")
            except Exception as e:
                self.logger.warning("Failed to cache analysis index", error=str(e))

    async def _fetch_proj_intel_items(
        self, since: Optional[datetime] = None, until: Optional[datetime] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch items from .proj-intel data."""
        if not self._proj_intel_manifest:
            return

        # Check if data is too old
        max_age_days = self.config.source_config.get("proj_intel_max_age_days", 7)
        generated_at_str = self._proj_intel_manifest.get("generated_at")
        if generated_at_str:
            try:
                generated_at = datetime.fromisoformat(
                    generated_at_str.replace("Z", "+00:00")
                )
                age_days = (datetime.now().astimezone() - generated_at).days
                if age_days > max_age_days:
                    self.logger.warning(
                        "Project intel data is old",
                        age_days=age_days,
                        max_age=max_age_days,
                    )
                    return
            except Exception as e:
                self.logger.warning(
                    "Failed to parse generated_at timestamp", error=str(e)
                )

        # Process different .proj-intel data types
        if self.config.source_config.get("ingest_file_elements", True):
            async for item in self._fetch_file_elements():
                yield item

        if self.config.source_config.get("ingest_project_analysis", True):
            async for item in self._fetch_project_analysis():
                yield item

        if self.config.source_config.get("ingest_symbol_index", True):
            async for item in self._fetch_symbol_data():
                yield item

    async def _fetch_file_elements(self) -> AsyncIterator[Dict[str, Any]]:
        """Fetch file element data from .proj-intel."""
        shards = self._proj_intel_manifest.get("shards", [])

        for shard in shards:
            if (
                shard.get("record_kind") == "min_file"
                and shard.get("name") == "file_elements.min"
            ):
                file_path = shard.get("path")
                if file_path:
                    async for item in self._process_jsonl_file(
                        file_path, "file_element"
                    ):
                        yield item

    async def _fetch_project_analysis(self) -> AsyncIterator[Dict[str, Any]]:
        """Fetch project analysis data from .proj-intel."""
        primary_file = self._proj_intel_manifest.get("primary")
        if primary_file:
            async for item in self._process_jsonl_file(
                primary_file, "project_analysis"
            ):
                yield item

    async def _fetch_symbol_data(self) -> AsyncIterator[Dict[str, Any]]:
        """Fetch symbol index data from .proj-intel."""
        symbol_index = self._proj_intel_cache.get("symbol_index")
        if symbol_index:
            # Convert symbol index to context items
            for symbol_type, symbols in symbol_index.items():
                if isinstance(symbols, dict):
                    for symbol_name, symbol_data in symbols.items():
                        yield {
                            "file_path": f"<symbol:{symbol_type}:{symbol_name}>",
                            "content": json.dumps(symbol_data, indent=2),
                            "title": f"{symbol_type.title()}: {symbol_name}",
                            "intel_data_type": "symbol",
                            "symbol_type": symbol_type,
                            "symbol_name": symbol_name,
                            "symbol_data": symbol_data,
                            "generated_at": self._proj_intel_manifest.get(
                                "generated_at"
                            ),
                        }

    async def _process_jsonl_file(
        self, file_path: str, data_type: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Process a JSONL file from .proj-intel."""
        try:
            # Find the actual file path
            actual_path = None
            proj_intel_paths = self.config.source_config.get(
                "proj_intel_paths", [".proj-intel"]
            )

            for intel_path in proj_intel_paths:
                test_path = Path(intel_path) / file_path.replace(".proj-intel/", "")
                if test_path.exists():
                    actual_path = test_path
                    break

                # Try relative to scan directories
                scan_dirs = self.config.source_config.get("scan_directories", ["."])
                for scan_dir in scan_dirs:
                    test_path = Path(scan_dir) / file_path
                    if test_path.exists():
                        actual_path = test_path
                        break

            if not actual_path:
                self.logger.warning("JSONL file not found", file_path=file_path)
                return

            # Process JSONL file line by line
            with open(actual_path, "r", encoding="utf-8") as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # Extract relevant information based on data type
                        if (
                            data_type == "file_element"
                            and data.get("type") == "collector_item"
                        ):
                            yield await self._transform_file_element(data)
                        elif data_type == "project_analysis":
                            yield await self._transform_project_analysis(data)

                    except json.JSONDecodeError as e:
                        self.logger.warning(
                            "Failed to parse JSONL line",
                            file_path=str(actual_path),
                            line_number=line_number,
                            error=str(e),
                        )
                    except Exception as e:
                        self.logger.error(
                            "Error processing JSONL line",
                            file_path=str(actual_path),
                            line_number=line_number,
                            error=str(e),
                        )

        except Exception as e:
            self.logger.error(
                "Failed to process JSONL file", file_path=file_path, error=str(e)
            )

    async def _transform_file_element(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform .proj-intel file element data into context item format."""
        file_data = data.get("data", {})
        file_path = file_data.get("path", "unknown")

        # Extract code intelligence data
        functions = file_data.get("functions", [])
        classes = file_data.get("classes", [])
        imports = file_data.get("imports", [])

        # Create content summary
        content_parts = []
        if functions:
            func_names = [f["name"] for f in functions]
            content_parts.append(f"Functions: {', '.join(func_names)}")
        if classes:
            class_names = [c["name"] for c in classes]
            content_parts.append(f"Classes: {', '.join(class_names)}")
        if imports:
            import_modules = [imp.get("module", str(imp)) for imp in imports]
            content_parts.append(
                f"Imports: {', '.join(import_modules[:10])}"
            )  # Limit for readability

        content = "\n".join(content_parts) if content_parts else f"File: {file_path}"

        return {
            "file_path": file_path,
            "content": content,
            "title": f"Code Intelligence: {Path(file_path).name}",
            "intel_data_type": "file_element",
            "line_count": file_data.get("line_count", 0),
            "content_hash": file_data.get("content_hash"),
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "generated_at": self._proj_intel_manifest.get("generated_at"),
            "code_analysis": {
                "function_count": len(functions),
                "class_count": len(classes),
                "import_count": len(imports),
                "complexity_indicators": {
                    "has_async": any(f.get("async", False) for f in functions),
                    "has_classes": len(classes) > 0,
                    "has_imports": len(imports) > 0,
                },
            },
        }

    async def _transform_project_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform .proj-intel project analysis data into context item format."""
        data_type = data.get("type", "unknown")
        collector = data.get("collector", "unknown")

        # Create a meaningful file path for this analysis item
        file_path = f"<analysis:{collector}:{data_type}>"

        # Extract the actual analysis data
        analysis_data = data.get("data", {})

        # Create readable content
        content = json.dumps(analysis_data, indent=2)

        return {
            "file_path": file_path,
            "content": content,
            "title": f"Project Analysis: {collector}",
            "intel_data_type": "project_analysis",
            "collector": collector,
            "analysis_type": data_type,
            "schema_version": data.get("schema_version"),
            "timestamp": data.get("timestamp"),
            "analysis_data": analysis_data,
            "generated_at": self._proj_intel_manifest.get("generated_at"),
        }

    def _setup_parsers(self) -> None:
        """Set up language-specific parsers."""
        # Basic parsers for common languages
        # In a full implementation, these would use proper AST parsers
        self._language_parsers = {
            "python": self._parse_python,
            "javascript": self._parse_javascript,
            "typescript": self._parse_typescript,
            "java": self._parse_java,
            "cpp": self._parse_cpp,
        }

    async def _scan_directory(
        self,
        directory: str,
        include_patterns: List[str],
        exclude_patterns: List[str],
        max_size_mb: int,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Scan directory for code files."""
        dir_path = Path(directory)
        if not dir_path.exists():
            return

        # Use pathlib to find matching files
        for pattern in include_patterns:
            for file_path in dir_path.rglob(pattern):
                if not file_path.is_file():
                    continue

                # Check exclusion patterns
                if self._is_excluded(str(file_path), exclude_patterns):
                    continue

                # Check file size
                try:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    if file_size_mb > max_size_mb:
                        self.logger.warning(
                            f"Skipping large file: {file_path} ({file_size_mb:.1f} MB)"
                        )
                        continue
                except OSError:
                    continue

                # Check modification time
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if since and mtime < since:
                        continue
                    if until and mtime > until:
                        continue
                except OSError:
                    continue

                # Check if file changed (if tracking changes)
                if self.config.source_config.get("track_changes", True):
                    if not await self._has_file_changed(file_path):
                        continue

                # Read and yield file content
                try:
                    item = await self._read_code_file(file_path)
                    if item:
                        yield item
                except Exception as e:
                    self.logger.error(f"Error reading file: {file_path}", error=str(e))

    def _is_excluded(self, file_path: str, exclude_patterns: List[str]) -> bool:
        """Check if file matches exclusion patterns."""
        path = Path(file_path)

        for pattern in exclude_patterns:
            # Convert glob pattern to path matching
            if pattern.endswith("/**"):
                # Directory exclusion
                dir_pattern = pattern[:-3]
                if dir_pattern in str(path):
                    return True
            elif "*" in pattern:
                # Glob pattern matching
                if path.match(pattern):
                    return True
            else:
                # Exact match
                if pattern in str(path):
                    return True

        return False

    async def _has_file_changed(self, file_path: Path) -> bool:
        """Check if file has changed since last processing."""
        file_str = str(file_path)

        try:
            # Calculate current checksum
            current_checksum = await self._calculate_file_checksum(file_path)

            # Compare with stored checksum
            if file_str in self._file_checksums:
                if self._file_checksums[file_str] == current_checksum:
                    return False

            # Update stored checksum
            self._file_checksums[file_str] = current_checksum
            return True

        except Exception:
            # If we can't calculate checksum, assume changed
            return True

    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        hash_sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    async def _read_code_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read code file and extract metadata."""
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
                self.logger.warning(
                    f"Could not read file with any encoding: {file_path}"
                )
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
            self.logger.error(f"Error reading file: {file_path}", error=str(e))
            return None

    def _detect_language(self, file_path: str, content: str) -> str:
        """Detect programming language from file path and content."""
        extension = Path(file_path).suffix.lower()

        # Extension-based detection
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".cxx": "cpp",
            ".cc": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".rs": "rust",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".sql": "sql",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".md": "markdown",
            ".sh": "shell",
            ".bash": "shell",
            ".zsh": "shell",
        }

        if extension in language_map:
            return language_map[extension]

        # Content-based detection for files without extensions
        if not extension:
            if content.startswith("#!/usr/bin/env python") or content.startswith(
                "#!/usr/bin/python"
            ):
                return "python"
            elif content.startswith("#!/bin/bash") or content.startswith("#!/bin/sh"):
                return "shell"
            elif "function" in content and "=>" in content:
                return "javascript"
            elif "class" in content and "def " in content:
                return "python"

        return "unknown"

    def _determine_entity_type(
        self, file_path: str, content: str, language: str
    ) -> str:
        """Determine the entity type based on file content."""
        # Check for specific patterns
        if "test" in file_path.lower():
            return "test_file"
        elif "config" in file_path.lower():
            return "config_file"
        elif file_path.endswith(".md"):
            return "documentation"
        elif file_path.endswith((".json", ".yaml", ".yml")):
            return "data_file"
        elif language in ["python", "javascript", "typescript", "java", "cpp", "c"]:
            if "class " in content:
                return "source_file_with_classes"
            elif "function " in content or "def " in content:
                return "source_file_with_functions"
            else:
                return "source_file"
        else:
            return "file"

    def _extract_functions(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Extract function definitions from code."""
        if language in self._language_parsers:
            return self._language_parsers[language](content, "functions")
        return self._extract_functions_generic(content)

    def _extract_classes(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Extract class definitions from code."""
        if language in self._language_parsers:
            return self._language_parsers[language](content, "classes")
        return self._extract_classes_generic(content)

    def _extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import statements from code."""
        if language in self._language_parsers:
            return self._language_parsers[language](content, "imports")
        return self._extract_imports_generic(content)

    def _extract_comments(self, content: str, language: str) -> List[str]:
        """Extract comments from code."""
        if language in self._language_parsers:
            return self._language_parsers[language](content, "comments")
        return self._extract_comments_generic(content)

    # Generic parsers (simple regex-based)

    def _extract_functions_generic(self, content: str) -> List[Dict[str, Any]]:
        """Generic function extraction."""
        import re

        functions = []

        # Python functions
        for match in re.finditer(r"^def\s+(\w+)\s*\([^)]*\):", content, re.MULTILINE):
            functions.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "type": "function",
                }
            )

        # JavaScript functions
        for match in re.finditer(
            r"function\s+(\w+)\s*\([^)]*\)", content, re.MULTILINE
        ):
            functions.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "type": "function",
                }
            )

        return functions

    def _extract_classes_generic(self, content: str) -> List[Dict[str, Any]]:
        """Generic class extraction."""
        import re

        classes = []

        # Python classes
        for match in re.finditer(
            r"^class\s+(\w+)(?:\([^)]*\))?:", content, re.MULTILINE
        ):
            classes.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "type": "class",
                }
            )

        return classes

    def _extract_imports_generic(self, content: str) -> List[str]:
        """Generic import extraction."""
        import re

        imports = []

        # Python imports
        for match in re.finditer(
            r"^(?:from\s+[\w.]+\s+)?import\s+(.+)$", content, re.MULTILINE
        ):
            imports.append(match.group(0).strip())

        # JavaScript imports
        for match in re.finditer(
            r'^import\s+.+from\s+[\'"]([^\'"]+)[\'"]', content, re.MULTILINE
        ):
            imports.append(match.group(0).strip())

        return imports

    def _extract_comments_generic(self, content: str) -> List[str]:
        """Generic comment extraction."""
        import re

        comments = []

        # Python comments
        for match in re.finditer(r"#.*$", content, re.MULTILINE):
            comment = match.group(0).strip()
            if len(comment) > 3:  # Skip very short comments
                comments.append(comment)

        # JavaScript/C-style comments
        for match in re.finditer(r"//.*$", content, re.MULTILINE):
            comment = match.group(0).strip()
            if len(comment) > 3:
                comments.append(comment)

        return comments

    def _matches_import(self, import_stmt: str, file_path: str) -> bool:
        """Check if import statement matches a file path."""
        # Simple matching - in a full implementation this would be more sophisticated
        file_name = Path(file_path).stem
        return file_name in import_stmt

    # Language-specific parsers (placeholder implementations)

    def _parse_python(self, content: str, extract_type: str) -> Any:
        """Parse Python code using AST with regex fallback."""
        try:
            tree = ast.parse(content)
            if extract_type == "functions":
                return self._extract_python_functions_ast(tree, content)
            elif extract_type == "classes":
                return self._extract_python_classes_ast(tree, content)
            elif extract_type == "imports":
                return self._extract_python_imports_ast(tree)
            elif extract_type == "comments":
                return self._extract_python_comments(content)
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            self.logger.warning("Python AST parsing failed, using regex fallback")
            if extract_type == "functions":
                return self._extract_functions_generic(content)
            elif extract_type == "classes":
                return self._extract_classes_generic(content)
            elif extract_type == "imports":
                return self._extract_imports_generic(content)
            elif extract_type == "comments":
                return self._extract_comments_generic(content)
        except Exception as e:
            self.logger.error(f"Python AST parsing error: {e}")
            return []
        return []

    def _parse_javascript(self, content: str, extract_type: str) -> Any:
        """Parse JavaScript code with enhanced regex patterns."""
        if extract_type == "functions":
            return self._extract_javascript_functions(content)
        elif extract_type == "classes":
            return self._extract_javascript_classes(content)
        elif extract_type == "imports":
            return self._extract_javascript_imports(content)
        elif extract_type == "comments":
            return self._extract_javascript_comments(content)
        return []

    def _parse_typescript(self, content: str, extract_type: str) -> Any:
        """Parse TypeScript code (placeholder)."""
        # Would use TypeScript compiler API
        return self._parse_python(content, extract_type)

    def _parse_java(self, content: str, extract_type: str) -> Any:
        """Parse Java code (placeholder)."""
        # Would use a Java parser like ANTLR
        return self._parse_python(content, extract_type)

    def _parse_cpp(self, content: str, extract_type: str) -> Any:
        """Parse C++ code (placeholder)."""
        # Would use a C++ parser like libclang
        return self._parse_python(content, extract_type)

    # JavaScript/TypeScript extractors

    def _extract_javascript_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript functions with enhanced patterns."""
        functions = []

        # Regular function declarations
        pattern = r"^\s*(async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*\{"
        for match in re.finditer(pattern, content, re.MULTILINE):
            is_async = bool(match.group(1))
            name = match.group(2)
            params = match.group(3).strip()
            line_no = content[: match.start()].count("\n") + 1

            functions.append(
                {
                    "name": name,
                    "line": line_no,
                    "type": "async_function" if is_async else "function",
                    "signature": f"{'async ' if is_async else ''}function {name}({params})",
                    "params": [p.strip() for p in params.split(",") if p.strip()],
                    "is_async": is_async,
                }
            )

        # Arrow functions assigned to variables
        pattern = r"^\s*(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\(([^)]*)\)\s*=>"
        for match in re.finditer(pattern, content, re.MULTILINE):
            is_async = bool(match.group(3))
            name = match.group(2)
            params = match.group(4).strip()
            line_no = content[: match.start()].count("\n") + 1

            functions.append(
                {
                    "name": name,
                    "line": line_no,
                    "type": "async_arrow_function" if is_async else "arrow_function",
                    "signature": f"{match.group(1)} {name} = {'async ' if is_async else ''}({params}) =>",
                    "params": [p.strip() for p in params.split(",") if p.strip()],
                    "is_async": is_async,
                }
            )

        return functions

    def _extract_javascript_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript classes."""
        classes = []

        pattern = r"^\s*class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{"
        for match in re.finditer(pattern, content, re.MULTILINE):
            name = match.group(1)
            extends = match.group(2)
            line_no = content[: match.start()].count("\n") + 1

            classes.append(
                {
                    "name": name,
                    "line": line_no,
                    "type": "class",
                    "extends": extends,
                    "signature": f"class {name}{' extends ' + extends if extends else ''}",
                }
            )

        return classes

    def _extract_javascript_imports(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript imports."""
        imports = []

        # ES6 import statements
        patterns = [
            r'^\s*import\s+(.+?)\s+from\s+["\']([^"\']+)["\']',
            r'^\s*import\s+["\']([^"\']+)["\']',
            r'^\s*const\s+(.+?)\s*=\s*require\s*\(\s*["\']([^"\']+)["\']\s*\)',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_no = content[: match.start()].count("\n") + 1
                if len(match.groups()) == 2:
                    imports.append(
                        {
                            "line": line_no,
                            "imported": match.group(1).strip(),
                            "module": match.group(2),
                            "statement": match.group(0).strip(),
                            "type": "require"
                            if "require" in match.group(0)
                            else "import",
                        }
                    )
                else:
                    imports.append(
                        {
                            "line": line_no,
                            "module": match.group(1),
                            "statement": match.group(0).strip(),
                            "type": "import",
                        }
                    )

        return imports

    def _extract_javascript_comments(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript comments."""
        comments = []
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith("//") and len(line) > 3:
                comments.append({"line": i, "text": line, "type": "line_comment"})

        # Multi-line comments
        pattern = r"/\*(.*?)\*/"
        for match in re.finditer(pattern, content, re.DOTALL):
            line_no = content[: match.start()].count("\n") + 1
            comments.append(
                {"line": line_no, "text": match.group(0), "type": "block_comment"}
            )

        return comments

    # Python AST-based extractors

    def _extract_python_functions_ast(
        self, tree: ast.AST, content: str
    ) -> List[Dict[str, Any]]:
        """Extract Python functions using AST."""
        functions = []
        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Extract docstring if available
                docstring = None
                if node.body and isinstance(node.body[0], ast.Expr):
                    value = node.body[0].value
                    if hasattr(value, "s"):  # Python < 3.8
                        docstring = value.s
                    elif hasattr(value, "value") and isinstance(
                        value.value, str
                    ):  # Python 3.8+
                        docstring = value.value

                # Extract arguments
                args = [arg.arg for arg in node.args.args]
                if hasattr(node.args, "posonlyargs"):  # Python 3.8+
                    args = [arg.arg for arg in node.args.posonlyargs] + args

                # Build signature
                signature = f"{'async ' if isinstance(node, ast.AsyncFunctionDef) else ''}def {node.name}({', '.join(args)})"

                functions.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": getattr(node, "end_lineno", None),
                        "type": "async_function"
                        if isinstance(node, ast.AsyncFunctionDef)
                        else "function",
                        "signature": signature,
                        "docstring": docstring,
                        "args": args,
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "decorators": [
                            self._ast_node_to_string(d) for d in node.decorator_list
                        ],
                    }
                )

        return functions

    def _extract_python_classes_ast(
        self, tree: ast.AST, content: str
    ) -> List[Dict[str, Any]]:
        """Extract Python classes using AST."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Extract docstring
                docstring = None
                if node.body and isinstance(node.body[0], ast.Expr):
                    value = node.body[0].value
                    if hasattr(value, "s"):  # Python < 3.8
                        docstring = value.s
                    elif hasattr(value, "value") and isinstance(
                        value.value, str
                    ):  # Python 3.8+
                        docstring = value.value

                # Extract base classes
                bases = []
                for base in node.bases:
                    bases.append(self._ast_node_to_string(base))

                # Extract methods
                methods = []
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(
                            {
                                "name": child.name,
                                "line": child.lineno,
                                "is_async": isinstance(child, ast.AsyncFunctionDef),
                                "is_classmethod": any(
                                    self._ast_node_to_string(d) == "classmethod"
                                    for d in child.decorator_list
                                ),
                                "is_staticmethod": any(
                                    self._ast_node_to_string(d) == "staticmethod"
                                    for d in child.decorator_list
                                ),
                            }
                        )

                classes.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": getattr(node, "end_lineno", None),
                        "type": "class",
                        "docstring": docstring,
                        "bases": bases,
                        "methods": methods,
                        "method_count": len(methods),
                    }
                )

        return classes

    def _extract_python_imports_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract Python imports using AST."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                            "statement": f"import {alias.name}{' as ' + alias.asname if alias.asname else ''}",
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        {
                            "type": "from_import",
                            "module": module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                            "level": node.level,
                            "statement": f"from {module} import {alias.name}{' as ' + alias.asname if alias.asname else ''}",
                        }
                    )

        return imports

    def _extract_python_comments(self, content: str) -> List[Dict[str, Any]]:
        """Extract Python comments."""
        comments = []
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith("#") and len(line) > 3:
                comments.append({"line": i, "text": line, "type": "line_comment"})

        return comments

    def _ast_node_to_string(self, node) -> str:
        """Convert AST node to string representation."""
        if hasattr(ast, "unparse"):  # Python 3.9+
            return ast.unparse(node)
        elif hasattr(node, "id"):
            return node.id
        elif hasattr(node, "attr"):
            return f"{self._ast_node_to_string(node.value)}.{node.attr}"
        elif hasattr(node, "n"):  # Python < 3.8 numbers
            return str(node.n)
        elif hasattr(node, "value"):  # Python 3.8+ constants
            return str(node.value)
        else:
            return str(node)

    # Advanced Symbol Extraction and Indexing

    def extract_symbols(
        self, content: str, file_path: str, language: str
    ) -> Dict[str, Any]:
        """Extract comprehensive symbol information from code."""
        symbols = {
            "file_path": file_path,
            "language": language,
            "functions": [],
            "classes": [],
            "variables": [],
            "constants": [],
            "imports": [],
            "exports": [],
            "type_definitions": [],
            "interface_definitions": [],
            "dependencies": [],
            "complexity_metrics": {},
        }

        try:
            if language == "python":
                symbols.update(self._extract_python_symbols(content, file_path))
            elif language in ["javascript", "typescript"]:
                symbols.update(
                    self._extract_js_ts_symbols(content, file_path, language)
                )
            elif language == "java":
                symbols.update(self._extract_java_symbols(content, file_path))
            elif language in ["cpp", "c"]:
                symbols.update(
                    self._extract_c_cpp_symbols(content, file_path, language)
                )
            elif language == "go":
                symbols.update(self._extract_go_symbols(content, file_path))
            elif language == "rust":
                symbols.update(self._extract_rust_symbols(content, file_path))
            else:
                # Generic symbol extraction for unsupported languages
                symbols.update(
                    self._extract_generic_symbols(content, file_path, language)
                )

            # Calculate complexity metrics
            symbols["complexity_metrics"] = self._calculate_complexity_metrics(
                symbols, content
            )

        except Exception as e:
            self.logger.error(f"Symbol extraction failed for {file_path}: {e}")

        return symbols

    def _extract_python_symbols(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract Python symbols using AST analysis."""
        symbols = {}

        try:
            tree = ast.parse(content)

            # Extract detailed function information
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_info = {
                        "name": node.name,
                        "line_start": node.lineno,
                        "line_end": getattr(node, "end_lineno", None),
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "is_generator": any(
                            isinstance(n, ast.Yield) or isinstance(n, ast.YieldFrom)
                            for n in ast.walk(node)
                        ),
                        "parameters": self._extract_python_parameters(node),
                        "return_annotation": self._ast_node_to_string(node.returns)
                        if node.returns
                        else None,
                        "decorators": [
                            self._ast_node_to_string(d) for d in node.decorator_list
                        ],
                        "docstring": self._extract_docstring(node),
                        "calls": self._extract_function_calls(node),
                        "variables_used": self._extract_variables_used(node),
                        "complexity_score": self._calculate_cyclomatic_complexity(node),
                    }
                    functions.append(func_info)

            symbols["functions"] = functions

            # Extract class information
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line_start": node.lineno,
                        "line_end": getattr(node, "end_lineno", None),
                        "base_classes": [
                            self._ast_node_to_string(base) for base in node.bases
                        ],
                        "decorators": [
                            self._ast_node_to_string(d) for d in node.decorator_list
                        ],
                        "docstring": self._extract_docstring(node),
                        "methods": self._extract_class_methods(node),
                        "properties": self._extract_class_properties(node),
                        "class_variables": self._extract_class_variables(node),
                    }
                    classes.append(class_info)

            symbols["classes"] = classes

            # Extract imports with detailed information
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_info = self._extract_detailed_import(node)
                    imports.extend(import_info)

            symbols["imports"] = imports

            # Extract module-level variables and constants
            variables, constants = self._extract_python_module_variables(tree)
            symbols["variables"] = variables
            symbols["constants"] = constants

        except SyntaxError as e:
            self.logger.warning(f"Python syntax error in {file_path}: {e}")

        return symbols

    def _extract_python_parameters(
        self, func_node: ast.FunctionDef
    ) -> List[Dict[str, Any]]:
        """Extract detailed parameter information from Python function."""
        parameters = []

        # Regular arguments
        for arg in func_node.args.args:
            param = {
                "name": arg.arg,
                "type_annotation": self._ast_node_to_string(arg.annotation)
                if arg.annotation
                else None,
                "kind": "positional",
            }
            parameters.append(param)

        # Positional-only arguments (Python 3.8+)
        if hasattr(func_node.args, "posonlyargs"):
            for arg in func_node.args.posonlyargs:
                param = {
                    "name": arg.arg,
                    "type_annotation": self._ast_node_to_string(arg.annotation)
                    if arg.annotation
                    else None,
                    "kind": "positional_only",
                }
                parameters.append(param)

        # Keyword-only arguments
        for arg in func_node.args.kwonlyargs:
            param = {
                "name": arg.arg,
                "type_annotation": self._ast_node_to_string(arg.annotation)
                if arg.annotation
                else None,
                "kind": "keyword_only",
            }
            parameters.append(param)

        # *args
        if func_node.args.vararg:
            param = {
                "name": func_node.args.vararg.arg,
                "type_annotation": self._ast_node_to_string(
                    func_node.args.vararg.annotation
                )
                if func_node.args.vararg.annotation
                else None,
                "kind": "var_positional",
            }
            parameters.append(param)

        # **kwargs
        if func_node.args.kwarg:
            param = {
                "name": func_node.args.kwarg.arg,
                "type_annotation": self._ast_node_to_string(
                    func_node.args.kwarg.annotation
                )
                if func_node.args.kwarg.annotation
                else None,
                "kind": "var_keyword",
            }
            parameters.append(param)

        return parameters

    def _extract_docstring(self, node) -> Optional[str]:
        """Extract docstring from a node."""
        if node.body and isinstance(node.body[0], ast.Expr):
            value = node.body[0].value
            if hasattr(value, "s"):  # Python < 3.8
                return value.s
            elif hasattr(value, "value") and isinstance(
                value.value, str
            ):  # Python 3.8+
                return value.value
        return None

    def _extract_function_calls(self, node) -> List[str]:
        """Extract function calls within a node."""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if hasattr(child.func, "id"):
                    calls.append(child.func.id)
                elif hasattr(child.func, "attr"):
                    calls.append(
                        f"{self._ast_node_to_string(child.func.value)}.{child.func.attr}"
                    )
        return list(set(calls))  # Remove duplicates

    def _extract_variables_used(self, node) -> List[str]:
        """Extract variables used within a node."""
        variables = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                variables.append(child.id)
        return list(set(variables))  # Remove duplicates

    def _calculate_cyclomatic_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):  # List/dict/set comprehensions
                complexity += 1

        return complexity

    def _extract_class_methods(self, class_node: ast.ClassDef) -> List[Dict[str, Any]]:
        """Extract methods from a class."""
        methods = []
        for child in class_node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = {
                    "name": child.name,
                    "line": child.lineno,
                    "is_async": isinstance(child, ast.AsyncFunctionDef),
                    "is_classmethod": any(
                        self._ast_node_to_string(d) == "classmethod"
                        for d in child.decorator_list
                    ),
                    "is_staticmethod": any(
                        self._ast_node_to_string(d) == "staticmethod"
                        for d in child.decorator_list
                    ),
                    "is_property": any(
                        self._ast_node_to_string(d) == "property"
                        for d in child.decorator_list
                    ),
                    "parameters": self._extract_python_parameters(child),
                    "docstring": self._extract_docstring(child),
                    "complexity_score": self._calculate_cyclomatic_complexity(child),
                }
                methods.append(method_info)
        return methods

    def _extract_class_properties(
        self, class_node: ast.ClassDef
    ) -> List[Dict[str, Any]]:
        """Extract properties from a class."""
        properties = []
        for child in class_node.body:
            if isinstance(child, ast.FunctionDef):
                if any(
                    self._ast_node_to_string(d) == "property"
                    for d in child.decorator_list
                ):
                    properties.append(
                        {
                            "name": child.name,
                            "line": child.lineno,
                            "docstring": self._extract_docstring(child),
                            "getter": True,
                            "setter": False,  # Would need more analysis
                            "deleter": False,  # Would need more analysis
                        }
                    )
        return properties

    def _extract_class_variables(
        self, class_node: ast.ClassDef
    ) -> List[Dict[str, Any]]:
        """Extract class variables."""
        variables = []
        for child in class_node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        variables.append(
                            {
                                "name": target.id,
                                "line": child.lineno,
                                "type_annotation": None,  # Class variables rarely have annotations
                                "is_constant": target.id.isupper(),
                            }
                        )
            elif isinstance(child, ast.AnnAssign) and isinstance(
                child.target, ast.Name
            ):
                variables.append(
                    {
                        "name": child.target.id,
                        "line": child.lineno,
                        "type_annotation": self._ast_node_to_string(child.annotation),
                        "is_constant": child.target.id.isupper(),
                    }
                )
        return variables

    def _extract_detailed_import(self, import_node) -> List[Dict[str, Any]]:
        """Extract detailed import information."""
        imports = []

        if isinstance(import_node, ast.Import):
            for alias in import_node.names:
                imports.append(
                    {
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": import_node.lineno,
                        "is_from_import": False,
                        "level": 0,
                    }
                )
        elif isinstance(import_node, ast.ImportFrom):
            module = import_node.module or ""
            for alias in import_node.names:
                imports.append(
                    {
                        "type": "from_import",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": import_node.lineno,
                        "is_from_import": True,
                        "level": import_node.level,
                        "is_star_import": alias.name == "*",
                    }
                )

        return imports

    def _extract_python_module_variables(self, tree) -> tuple:
        """Extract module-level variables and constants."""
        variables = []
        constants = []

        # Only look at top-level assignments
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_info = {
                            "name": target.id,
                            "line": node.lineno,
                            "type_annotation": None,
                            "is_constant": target.id.isupper(),
                        }
                        if target.id.isupper():
                            constants.append(var_info)
                        else:
                            variables.append(var_info)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                var_info = {
                    "name": node.target.id,
                    "line": node.lineno,
                    "type_annotation": self._ast_node_to_string(node.annotation),
                    "is_constant": node.target.id.isupper(),
                }
                if node.target.id.isupper():
                    constants.append(var_info)
                else:
                    variables.append(var_info)

        return variables, constants

    def _calculate_complexity_metrics(
        self, symbols: Dict[str, Any], content: str
    ) -> Dict[str, Any]:
        """Calculate various complexity metrics for the file."""
        lines = content.splitlines()

        metrics = {
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
            "function_count": len(symbols.get("functions", [])),
            "class_count": len(symbols.get("classes", [])),
            "import_count": len(symbols.get("imports", [])),
            "avg_function_complexity": 0,
            "max_function_complexity": 0,
            "total_cyclomatic_complexity": 0,
        }

        # Calculate complexity statistics
        if symbols.get("functions"):
            complexities = [f.get("complexity_score", 1) for f in symbols["functions"]]
            metrics["avg_function_complexity"] = sum(complexities) / len(complexities)
            metrics["max_function_complexity"] = max(complexities)
            metrics["total_cyclomatic_complexity"] = sum(complexities)

        return metrics

    # Enhanced Relationship Detection

    def detect_enhanced_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Enhanced relationship detection using detailed symbol analysis."""
        relationships = []

        # Use the existing relationship detection as base
        base_relationships = self.detect_relationships(item, context_window)
        relationships.extend(base_relationships)

        # Add enhanced relationships based on detailed symbols
        if item.metrics and item.metrics.get("detailed_symbols"):
            detailed_symbols = item.metrics["detailed_symbols"]
            enhanced_rels = self._detect_symbol_based_relationships(
                item, detailed_symbols, context_window
            )
            relationships.extend(enhanced_rels)

        # Detect complexity-based relationships
        complexity_rels = self._detect_complexity_relationships(item, context_window)
        relationships.extend(complexity_rels)

        # Detect architectural patterns
        pattern_rels = self._detect_architectural_patterns(item, context_window)
        relationships.extend(pattern_rels)

        return relationships

    def _detect_symbol_based_relationships(
        self,
        item: ContextItem,
        symbols: Dict[str, Any],
        context_window: List[ContextItem],
    ) -> List[tuple]:
        """Detect relationships based on detailed symbol analysis."""
        relationships = []

        for context_item in context_window:
            if context_item.id == item.id:
                continue

            context_symbols = None
            if context_item.metrics and context_item.metrics.get("detailed_symbols"):
                context_symbols = context_item.metrics["detailed_symbols"]

            if not context_symbols:
                continue

            # Function call relationships
            relationships.extend(
                self._detect_function_call_relationships(
                    item, symbols, context_item, context_symbols
                )
            )

            # Inheritance relationships
            relationships.extend(
                self._detect_inheritance_relationships(
                    item, symbols, context_item, context_symbols
                )
            )

            # Import usage relationships
            relationships.extend(
                self._detect_import_usage_relationships(
                    item, symbols, context_item, context_symbols
                )
            )

            # Interface/Protocol relationships
            relationships.extend(
                self._detect_interface_relationships(
                    item, symbols, context_item, context_symbols
                )
            )

            # Data flow relationships
            relationships.extend(
                self._detect_data_flow_relationships(
                    item, symbols, context_item, context_symbols
                )
            )

        return relationships

    def _detect_function_call_relationships(
        self,
        item: ContextItem,
        symbols: Dict[str, Any],
        context_item: ContextItem,
        context_symbols: Dict[str, Any],
    ) -> List[tuple]:
        """Detect function call relationships between files."""
        relationships = []

        # Check if functions in item call functions defined in context_item
        for function in symbols.get("functions", []):
            function_calls = function.get("calls", [])

            for context_function in context_symbols.get("functions", []):
                if context_function["name"] in function_calls:
                    relationships.append(
                        (
                            "calls_function",
                            context_item.id,
                            0.9,
                            {
                                "caller": function["name"],
                                "callee": context_function["name"],
                                "caller_line": function.get("line_start"),
                                "callee_line": context_function.get("line_start"),
                            },
                        )
                    )

        return relationships

    def _detect_inheritance_relationships(
        self,
        item: ContextItem,
        symbols: Dict[str, Any],
        context_item: ContextItem,
        context_symbols: Dict[str, Any],
    ) -> List[tuple]:
        """Detect class inheritance relationships."""
        relationships = []

        # Check if classes in item inherit from classes in context_item
        for cls in symbols.get("classes", []):
            base_classes = cls.get("base_classes", [])

            for context_class in context_symbols.get("classes", []):
                if context_class["name"] in base_classes:
                    relationships.append(
                        (
                            "inherits_from",
                            context_item.id,
                            0.95,
                            {
                                "child_class": cls["name"],
                                "parent_class": context_class["name"],
                                "child_line": cls.get("line_start"),
                                "parent_line": context_class.get("line_start"),
                            },
                        )
                    )

        return relationships

    def _detect_import_usage_relationships(
        self,
        item: ContextItem,
        symbols: Dict[str, Any],
        context_item: ContextItem,
        context_symbols: Dict[str, Any],
    ) -> List[tuple]:
        """Detect import and usage relationships."""
        relationships = []

        # Check if item imports modules/symbols from context_item
        item_file_path = item.file_path
        context_file_path = context_item.file_path

        if not item_file_path or not context_file_path:
            return relationships

        context_module_name = Path(context_file_path).stem

        for import_info in symbols.get("imports", []):
            imported_module = import_info.get("module", "")
            imported_name = import_info.get("name", "")

            # Check for direct module import
            if (
                context_module_name in imported_module
                or imported_module in context_module_name
            ):
                relationships.append(
                    (
                        "imports_module",
                        context_item.id,
                        0.85,
                        {
                            "import_statement": import_info.get("statement", ""),
                            "import_line": import_info.get("line"),
                            "import_type": import_info.get("type"),
                        },
                    )
                )

            # Check for specific symbol import
            for context_function in context_symbols.get("functions", []):
                if imported_name == context_function["name"]:
                    relationships.append(
                        (
                            "imports_symbol",
                            context_item.id,
                            0.9,
                            {
                                "symbol_name": imported_name,
                                "symbol_type": "function",
                                "import_line": import_info.get("line"),
                                "symbol_line": context_function.get("line_start"),
                            },
                        )
                    )

            for context_class in context_symbols.get("classes", []):
                if imported_name == context_class["name"]:
                    relationships.append(
                        (
                            "imports_symbol",
                            context_item.id,
                            0.9,
                            {
                                "symbol_name": imported_name,
                                "symbol_type": "class",
                                "import_line": import_info.get("line"),
                                "symbol_line": context_class.get("line_start"),
                            },
                        )
                    )

        return relationships

    def _detect_interface_relationships(
        self,
        item: ContextItem,
        symbols: Dict[str, Any],
        context_item: ContextItem,
        context_symbols: Dict[str, Any],
    ) -> List[tuple]:
        """Detect interface implementation relationships."""
        relationships = []

        # This is more relevant for languages like TypeScript, Java, C#
        # For Python, check for duck typing patterns or Protocol usage

        # Check for method signature similarities (duck typing)
        for cls in symbols.get("classes", []):
            cls_methods = cls.get("methods", [])

            for context_class in context_symbols.get("classes", []):
                context_methods = context_class.get("methods", [])

                # Find common method names
                cls_method_names = {m["name"] for m in cls_methods}
                context_method_names = {m["name"] for m in context_methods}

                common_methods = cls_method_names & context_method_names

                if len(common_methods) >= 2:  # Threshold for interface similarity
                    confidence = min(0.8, len(common_methods) * 0.2)
                    relationships.append(
                        (
                            "implements_interface",
                            context_item.id,
                            confidence,
                            {
                                "implementing_class": cls["name"],
                                "interface_class": context_class["name"],
                                "common_methods": list(common_methods),
                                "similarity_score": len(common_methods)
                                / len(cls_method_names.union(context_method_names)),
                            },
                        )
                    )

        return relationships

    def _detect_data_flow_relationships(
        self,
        item: ContextItem,
        symbols: Dict[str, Any],
        context_item: ContextItem,
        context_symbols: Dict[str, Any],
    ) -> List[tuple]:
        """Detect data flow relationships between files."""
        relationships = []

        # Check for shared data structures or constants
        item_constants = {c["name"] for c in symbols.get("constants", [])}
        context_constants = {c["name"] for c in context_symbols.get("constants", [])}

        shared_constants = item_constants & context_constants
        if shared_constants:
            relationships.append(
                (
                    "shares_constants",
                    context_item.id,
                    0.7,
                    {
                        "shared_constants": list(shared_constants),
                        "count": len(shared_constants),
                    },
                )
            )

        # Check for variable usage patterns
        for function in symbols.get("functions", []):
            variables_used = set(function.get("variables_used", []))

            for context_function in context_symbols.get("functions", []):
                context_variables = set(context_function.get("variables_used", []))

                # Check for similar variable usage patterns
                common_vars = variables_used & context_variables
                if len(common_vars) >= 3:  # Threshold for data flow relationship
                    relationships.append(
                        (
                            "similar_data_usage",
                            context_item.id,
                            0.6,
                            {
                                "function1": function["name"],
                                "function2": context_function["name"],
                                "common_variables": list(common_vars),
                                "similarity_score": len(common_vars)
                                / len(variables_used.union(context_variables)),
                            },
                        )
                    )

        return relationships

    def _detect_complexity_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships based on complexity patterns."""
        relationships = []

        if not item.metrics or not item.metrics.get("total_cyclomatic_complexity"):
            return relationships

        item_complexity = item.metrics.get("total_cyclomatic_complexity", 0)

        for context_item in context_window:
            if (
                context_item.id == item.id
                or not context_item.metrics
                or not context_item.metrics.get("total_cyclomatic_complexity")
            ):
                continue

            context_complexity = context_item.metrics.get(
                "total_cyclomatic_complexity", 0
            )

            # Files with similar complexity might be related
            if abs(item_complexity - context_complexity) <= 2 and item_complexity > 5:
                confidence = max(
                    0.3, 0.7 - abs(item_complexity - context_complexity) * 0.1
                )
                relationships.append(
                    (
                        "similar_complexity",
                        context_item.id,
                        confidence,
                        {
                            "item_complexity": item_complexity,
                            "context_complexity": context_complexity,
                            "complexity_difference": abs(
                                item_complexity - context_complexity
                            ),
                        },
                    )
                )

        return relationships

    def _detect_architectural_patterns(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect architectural pattern relationships."""
        relationships = []

        item_pattern = self._identify_architectural_pattern(item)
        if not item_pattern:
            return relationships

        for context_item in context_window:
            if context_item.id == item.id:
                continue

            context_pattern = self._identify_architectural_pattern(context_item)

            if context_pattern and item_pattern == context_pattern:
                relationships.append(
                    (
                        "same_architectural_pattern",
                        context_item.id,
                        0.75,
                        {"pattern": item_pattern, "pattern_confidence": 0.8},
                    )
                )

        return relationships

    def _identify_architectural_pattern(self, item: ContextItem) -> Optional[str]:
        """Identify architectural patterns in code."""
        if not item.metrics:
            return None

        file_path = item.file_path or ""
        file_name = Path(file_path).name.lower()

        # Pattern detection based on file naming and structure
        if "controller" in file_name or "handler" in file_name:
            return "controller"
        elif "service" in file_name or "manager" in file_name:
            return "service"
        elif "model" in file_name or "entity" in file_name:
            return "model"
        elif "dao" in file_name or "repository" in file_name:
            return "repository"
        elif "factory" in file_name:
            return "factory"
        elif "adapter" in file_name:
            return "adapter"
        elif "util" in file_name or "helper" in file_name:
            return "utility"
        elif "test" in file_name:
            return "test"
        elif "config" in file_name or "settings" in file_name:
            return "configuration"

        # Pattern detection based on code structure
        detailed_symbols = item.metrics.get("detailed_symbols")
        if detailed_symbols:
            functions = detailed_symbols.get("functions", [])
            classes = detailed_symbols.get("classes", [])

            # Check for decorator patterns
            if any("@" in str(f.get("decorators", [])) for f in functions):
                return "decorator_pattern"

            # Check for singleton pattern
            if any(c["name"].endswith("Singleton") for c in classes):
                return "singleton"

            # Check for observer pattern
            if any(
                "observer" in c["name"].lower() or "listener" in c["name"].lower()
                for c in classes
            ):
                return "observer"

        return None

    # Incremental Analysis Support

    def enable_incremental_analysis(self, watch_directories: List[str] = None):
        """Enable incremental analysis with file watching."""
        if not watch_directories:
            watch_directories = self.config.source_config.get("scan_directories", ["."])

        self._watch_directories = watch_directories
        self._incremental_enabled = True
        self.logger.info(
            f"Incremental analysis enabled for directories: {watch_directories}"
        )

    def get_changed_files_since(self, since: datetime) -> List[str]:
        """Get list of files that have changed since the given timestamp."""
        changed_files = []

        scan_dirs = self.config.source_config.get("scan_directories", ["."])
        include_patterns = self.config.source_config.get("include_patterns", ["*"])
        exclude_patterns = self.config.source_config.get("exclude_patterns", [])

        for directory in scan_dirs:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue

            for pattern in include_patterns:
                for file_path in dir_path.rglob(pattern):
                    if not file_path.is_file():
                        continue

                    if self._is_excluded(str(file_path), exclude_patterns):
                        continue

                    try:
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mtime > since:
                            changed_files.append(str(file_path))
                    except OSError:
                        continue

        return changed_files

    def invalidate_cache_for_files(self, file_paths: List[str]):
        """Invalidate caches for specific files."""
        for file_path in file_paths:
            # Remove from checksum cache
            if file_path in self._file_checksums:
                del self._file_checksums[file_path]

            # Remove from processed files
            if file_path in self._processed_files:
                self._processed_files.remove(file_path)

        self.logger.info(f"Invalidated cache for {len(file_paths)} files")

    async def fetch_incremental_items(
        self, since: datetime, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch only items that have changed since the given timestamp."""
        if not hasattr(self, "_incremental_enabled") or not self._incremental_enabled:
            # Fall back to full fetch
            async for item in self.fetch_items(since=since, limit=limit):
                yield item
            return

        # Get changed files
        changed_files = self.get_changed_files_since(since)

        if not changed_files:
            self.logger.info("No files changed since last incremental update")
            return

        self.logger.info(f"Processing {len(changed_files)} changed files")

        # Invalidate caches for changed files
        self.invalidate_cache_for_files(changed_files)

        # Process changed files
        count = 0
        for file_path in changed_files:
            if limit and count >= limit:
                break

            try:
                item = await self._read_code_file(Path(file_path))
                if item:
                    yield item
                    count += 1
            except Exception as e:
                self.logger.error(
                    f"Error processing changed file: {file_path}", error=str(e)
                )
