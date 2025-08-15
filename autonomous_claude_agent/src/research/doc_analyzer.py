"""
Documentation Analyzer for parsing and extracting insights.

Provides async document analysis capabilities for various formats
including HTML, Markdown, PDF, and code documentation.

Author: Autonomous Claude Agent
Created: 2025-08-15
"""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import aiofiles
from bs4 import BeautifulSoup, Tag

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types."""

    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    YAML = "yaml"
    CODE = "code"
    TEXT = "text"
    DOCSTRING = "docstring"
    API_SPEC = "api_spec"


class InsightType(Enum):
    """Types of insights extracted from documents."""

    SUMMARY = "summary"
    KEY_CONCEPT = "key_concept"
    CODE_EXAMPLE = "code_example"
    API_ENDPOINT = "api_endpoint"
    PARAMETER = "parameter"
    RETURN_VALUE = "return_value"
    WARNING = "warning"
    BEST_PRACTICE = "best_practice"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE_TIP = "performance_tip"


@dataclass
class AnalysisConfig:
    """Configuration for document analysis."""

    extract_code_samples: bool = True
    extract_api_info: bool = True
    extract_parameters: bool = True
    extract_examples: bool = True
    extract_warnings: bool = True
    extract_dependencies: bool = True
    max_depth: int = 3  # For nested structure analysis
    cache_ttl: int = 7200  # 2 hours
    timeout: int = 30
    min_relevance_score: float = 0.5
    language_detection: bool = True
    sentiment_analysis: bool = False


@dataclass
class DocumentInsight:
    """Individual insight extracted from document."""

    type: InsightType
    content: str
    relevance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_line: Optional[int] = None
    source_section: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
            "source_line": self.source_line,
            "source_section": self.source_section,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DocumentAnalysis:
    """Complete analysis result for a document."""

    document_id: str
    document_type: DocumentType
    title: Optional[str]
    summary: str
    insights: List[DocumentInsight]
    structure: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "document_type": self.document_type.value,
            "title": self.title,
            "summary": self.summary,
            "insights": [i.to_dict() for i in self.insights],
            "structure": self.structure,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "processing_time": self.processing_time,
        }


class DocumentAnalyzer:
    """Async document analyzer for extracting structured insights."""

    def __init__(
        self, config: Optional[AnalysisConfig] = None, cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize document analyzer.

        Args:
            config: Analysis configuration
            cache_manager: Cache manager instance
        """
        self.config = config or AnalysisConfig()
        self.cache = cache_manager or CacheManager()
        self._patterns = self._compile_patterns()

        logger.info("DocumentAnalyzer initialized")

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for content extraction."""
        return {
            "code_block": re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL),
            "inline_code": re.compile(r"`([^`]+)`"),
            "url": re.compile(r"https?://[^\s<>\"]+"),
            "api_endpoint": re.compile(r"(GET|POST|PUT|DELETE|PATCH)\s+(/[\w/{}:-]+)"),
            "parameter": re.compile(
                r"(?:param|parameter|arg|argument)\s+(\w+):\s*(.+?)(?:\n|$)", re.IGNORECASE
            ),
            "return_value": re.compile(
                r"(?:returns?|return value):\s*(.+?)(?:\n|$)", re.IGNORECASE
            ),
            "warning": re.compile(
                r"(?:warning|caution|important|note):\s*(.+?)(?:\n|$)", re.IGNORECASE
            ),
            "todo": re.compile(r"(?:TODO|FIXME|HACK|NOTE):\s*(.+?)(?:\n|$)"),
            "version": re.compile(r"(?:version|v)\s*([\d.]+)", re.IGNORECASE),
            "import": re.compile(r"(?:import|from|require|include)\s+([\w.]+)"),
            "function_def": re.compile(r"(?:def|function|func|fn)\s+(\w+)\s*\(([^)]*)\)"),
            "class_def": re.compile(r"(?:class|struct|interface)\s+(\w+)"),
        }

    def _get_cache_key(self, content: str, doc_type: DocumentType) -> str:
        """Generate cache key for document."""
        key_string = f"{doc_type.value}:{content[:1000]}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def analyze(
        self, content: Union[str, Path], doc_type: Optional[DocumentType] = None, **kwargs
    ) -> DocumentAnalysis:
        """
        Analyze document and extract insights.

        Args:
            content: Document content or path
            doc_type: Document type (auto-detected if None)
            **kwargs: Additional analysis parameters

        Returns:
            Document analysis result
        """
        start_time = datetime.now()

        # Load content if path
        if isinstance(content, Path):
            content = await self._load_file(content)

        # Auto-detect document type
        if doc_type is None:
            doc_type = self._detect_document_type(content)

        # Check cache
        cache_key = self._get_cache_key(content, doc_type)
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for document analysis")
            return DocumentAnalysis(**cached_result)

        # Perform analysis
        try:
            if doc_type == DocumentType.MARKDOWN:
                analysis = await self._analyze_markdown(content, **kwargs)
            elif doc_type == DocumentType.HTML:
                analysis = await self._analyze_html(content, **kwargs)
            elif doc_type == DocumentType.JSON:
                analysis = await self._analyze_json(content, **kwargs)
            elif doc_type == DocumentType.CODE:
                analysis = await self._analyze_code(content, **kwargs)
            elif doc_type == DocumentType.API_SPEC:
                analysis = await self._analyze_api_spec(content, **kwargs)
            else:
                analysis = await self._analyze_text(content, **kwargs)

            # Calculate processing time
            analysis.processing_time = (datetime.now() - start_time).total_seconds()

            # Cache result
            await self.cache.set(cache_key, analysis.to_dict(), ttl=self.config.cache_ttl)

            return analysis

        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            raise

    async def _load_file(self, path: Path) -> str:
        """Load file content asynchronously."""
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()

    def _detect_document_type(self, content: str) -> DocumentType:
        """Auto-detect document type from content."""
        content_lower = content[:1000].lower()

        if content.strip().startswith("{") or content.strip().startswith("["):
            return DocumentType.JSON
        elif content.strip().startswith("---") and "openapi" in content_lower:
            return DocumentType.API_SPEC
        elif "```" in content or "##" in content or "**" in content:
            return DocumentType.MARKDOWN
        elif "<html" in content_lower or "<body" in content_lower:
            return DocumentType.HTML
        elif "def " in content or "class " in content or "import " in content:
            return DocumentType.CODE
        else:
            return DocumentType.TEXT

    async def _analyze_markdown(self, content: str, **kwargs) -> DocumentAnalysis:
        """Analyze Markdown document."""
        insights = []
        structure = {"sections": [], "code_blocks": [], "links": []}

        # Extract title
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else None

        # Extract sections
        sections = re.findall(r"^#{1,6}\s+(.+)$", content, re.MULTILINE)
        structure["sections"] = sections

        # Extract code blocks
        if self.config.extract_code_samples:
            code_blocks = self._patterns["code_block"].findall(content)
            for lang, code in code_blocks:
                insight = DocumentInsight(
                    type=InsightType.CODE_EXAMPLE,
                    content=code.strip(),
                    metadata={"language": lang or "unknown"},
                )
                insights.append(insight)
                structure["code_blocks"].append(
                    {"language": lang, "lines": len(code.strip().split("\n"))}
                )

        # Extract warnings and notes
        if self.config.extract_warnings:
            warnings = self._patterns["warning"].findall(content)
            for warning in warnings:
                insight = DocumentInsight(type=InsightType.WARNING, content=warning.strip())
                insights.append(insight)

        # Extract URLs
        urls = self._patterns["url"].findall(content)
        structure["links"] = urls

        # Generate summary
        summary = self._generate_summary(content, max_length=200)

        return DocumentAnalysis(
            document_id=hashlib.md5(content.encode()).hexdigest(),
            document_type=DocumentType.MARKDOWN,
            title=title,
            summary=summary,
            insights=insights,
            structure=structure,
            metadata={
                "total_lines": len(content.split("\n")),
                "total_sections": len(sections),
                "total_code_blocks": len(structure["code_blocks"]),
                "total_links": len(urls),
            },
        )

    async def _analyze_html(self, content: str, **kwargs) -> DocumentAnalysis:
        """Analyze HTML document."""
        insights = []
        structure = {"tags": {}, "links": [], "scripts": [], "styles": []}

        soup = BeautifulSoup(content, "html.parser")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.text if title_tag else None

        # Count tags
        for tag in soup.find_all():
            tag_name = tag.name
            if tag_name not in structure["tags"]:
                structure["tags"][tag_name] = 0
            structure["tags"][tag_name] += 1

        # Extract links
        for link in soup.find_all("a", href=True):
            structure["links"].append(link["href"])

        # Extract scripts
        for script in soup.find_all("script"):
            if script.get("src"):
                structure["scripts"].append(script["src"])

        # Extract code examples
        if self.config.extract_code_samples:
            for code in soup.find_all(["code", "pre"]):
                insight = DocumentInsight(
                    type=InsightType.CODE_EXAMPLE,
                    content=code.text.strip(),
                    metadata={"tag": code.name},
                )
                insights.append(insight)

        # Extract main content
        main_content = soup.get_text(separator=" ", strip=True)
        summary = self._generate_summary(main_content, max_length=200)

        return DocumentAnalysis(
            document_id=hashlib.md5(content.encode()).hexdigest(),
            document_type=DocumentType.HTML,
            title=title,
            summary=summary,
            insights=insights,
            structure=structure,
            metadata={
                "total_tags": sum(structure["tags"].values()),
                "unique_tags": len(structure["tags"]),
                "total_links": len(structure["links"]),
                "total_scripts": len(structure["scripts"]),
            },
        )

    async def _analyze_json(self, content: str, **kwargs) -> DocumentAnalysis:
        """Analyze JSON document."""
        insights = []
        structure = {}

        try:
            data = json.loads(content)
            structure = self._analyze_json_structure(data)

            # Extract API endpoints if present
            if self.config.extract_api_info:
                endpoints = self._extract_api_endpoints(data)
                for endpoint in endpoints:
                    insight = DocumentInsight(
                        type=InsightType.API_ENDPOINT,
                        content=f"{endpoint['method']} {endpoint['path']}",
                        metadata=endpoint,
                    )
                    insights.append(insight)

            # Extract configuration values
            configs = self._extract_configurations(data)
            for key, value in configs.items():
                insight = DocumentInsight(
                    type=InsightType.CONFIGURATION,
                    content=f"{key}: {value}",
                    metadata={"key": key, "value": value},
                )
                insights.append(insight)

            summary = f"JSON document with {len(structure.get('keys', []))} root keys"

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            summary = "Invalid JSON document"
            structure = {"error": str(e)}

        return DocumentAnalysis(
            document_id=hashlib.md5(content.encode()).hexdigest(),
            document_type=DocumentType.JSON,
            title=None,
            summary=summary,
            insights=insights,
            structure=structure,
            metadata={"size_bytes": len(content), "valid_json": "error" not in structure},
        )

    async def _analyze_code(self, content: str, **kwargs) -> DocumentAnalysis:
        """Analyze source code."""
        insights = []
        structure = {"functions": [], "classes": [], "imports": [], "comments": []}

        # Extract functions
        functions = self._patterns["function_def"].findall(content)
        for func_name, params in functions:
            structure["functions"].append(
                {
                    "name": func_name,
                    "parameters": [p.strip() for p in params.split(",") if p.strip()],
                }
            )

            if self.config.extract_parameters:
                insight = DocumentInsight(
                    type=InsightType.PARAMETER,
                    content=f"Function {func_name}({params})",
                    metadata={"function": func_name, "params": params},
                )
                insights.append(insight)

        # Extract classes
        classes = self._patterns["class_def"].findall(content)
        for class_name in classes:
            structure["classes"].append(class_name)

        # Extract imports/dependencies
        if self.config.extract_dependencies:
            imports = self._patterns["import"].findall(content)
            structure["imports"] = list(set(imports))

            for imp in set(imports):
                insight = DocumentInsight(
                    type=InsightType.DEPENDENCY, content=imp, metadata={"type": "import"}
                )
                insights.append(insight)

        # Extract TODOs and FIXMEs
        todos = self._patterns["todo"].findall(content)
        for todo in todos:
            insight = DocumentInsight(
                type=InsightType.WARNING, content=todo.strip(), metadata={"type": "todo"}
            )
            insights.append(insight)

        # Generate summary
        summary = (
            f"Code with {len(structure['functions'])} functions, "
            f"{len(structure['classes'])} classes, "
            f"{len(structure['imports'])} imports"
        )

        return DocumentAnalysis(
            document_id=hashlib.md5(content.encode()).hexdigest(),
            document_type=DocumentType.CODE,
            title=kwargs.get("filename"),
            summary=summary,
            insights=insights,
            structure=structure,
            metadata={
                "total_lines": len(content.split("\n")),
                "language": kwargs.get("language", "unknown"),
            },
        )

    async def _analyze_api_spec(self, content: str, **kwargs) -> DocumentAnalysis:
        """Analyze API specification (OpenAPI/Swagger)."""
        insights = []
        structure = {"endpoints": [], "schemas": [], "security": []}

        try:
            # Try to parse as YAML or JSON
            if content.strip().startswith("{"):
                spec = json.loads(content)
            else:
                import yaml

                spec = yaml.safe_load(content)

            # Extract API info
            info = spec.get("info", {})
            title = info.get("title", "Unknown API")
            version = info.get("version", "unknown")

            # Extract endpoints
            paths = spec.get("paths", {})
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method in ["get", "post", "put", "delete", "patch"]:
                        endpoint = {
                            "path": path,
                            "method": method.upper(),
                            "summary": details.get("summary", ""),
                            "parameters": details.get("parameters", []),
                        }
                        structure["endpoints"].append(endpoint)

                        insight = DocumentInsight(
                            type=InsightType.API_ENDPOINT,
                            content=f"{method.upper()} {path}",
                            metadata=endpoint,
                        )
                        insights.append(insight)

            # Extract schemas
            schemas = spec.get("components", {}).get("schemas", {})
            structure["schemas"] = list(schemas.keys())

            summary = (
                f"API v{version} with {len(structure['endpoints'])} endpoints "
                f"and {len(structure['schemas'])} schemas"
            )

        except Exception as e:
            logger.error(f"Failed to parse API spec: {e}")
            summary = "Invalid API specification"
            title = None

        return DocumentAnalysis(
            document_id=hashlib.md5(content.encode()).hexdigest(),
            document_type=DocumentType.API_SPEC,
            title=title,
            summary=summary,
            insights=insights,
            structure=structure,
            metadata={
                "api_version": version if "version" in locals() else None,
                "total_endpoints": len(structure["endpoints"]),
                "total_schemas": len(structure["schemas"]),
            },
        )

    async def _analyze_text(self, content: str, **kwargs) -> DocumentAnalysis:
        """Analyze plain text document."""
        insights = []
        structure = {"paragraphs": [], "sentences": 0, "words": 0}

        # Basic text analysis
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        structure["paragraphs"] = [p[:100] + "..." if len(p) > 100 else p for p in paragraphs]
        structure["sentences"] = len(re.findall(r"[.!?]+", content))
        structure["words"] = len(content.split())

        # Extract key concepts (simple keyword extraction)
        keywords = self._extract_keywords(content)
        for keyword in keywords[:10]:  # Top 10 keywords
            insight = DocumentInsight(
                type=InsightType.KEY_CONCEPT, content=keyword, relevance_score=0.8
            )
            insights.append(insight)

        summary = self._generate_summary(content, max_length=200)

        return DocumentAnalysis(
            document_id=hashlib.md5(content.encode()).hexdigest(),
            document_type=DocumentType.TEXT,
            title=None,
            summary=summary,
            insights=insights,
            structure=structure,
            metadata={
                "total_paragraphs": len(paragraphs),
                "total_sentences": structure["sentences"],
                "total_words": structure["words"],
                "avg_paragraph_length": structure["words"] / len(paragraphs) if paragraphs else 0,
            },
        )

    def _analyze_json_structure(self, data: Any, depth: int = 0) -> Dict[str, Any]:
        """Recursively analyze JSON structure."""
        if depth > self.config.max_depth:
            return {"truncated": True}

        if isinstance(data, dict):
            return {
                "type": "object",
                "keys": list(data.keys()),
                "children": {
                    k: self._analyze_json_structure(v, depth + 1)
                    for k, v in list(data.items())[:10]  # Limit to 10 items
                },
            }
        elif isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "sample": self._analyze_json_structure(data[0], depth + 1) if data else None,
            }
        else:
            return {"type": type(data).__name__, "value": str(data)[:100]}

    def _extract_api_endpoints(self, data: Any) -> List[Dict[str, Any]]:
        """Extract API endpoints from JSON data."""
        endpoints = []

        def traverse(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ["paths", "routes", "endpoints"]:
                        if isinstance(value, dict):
                            for endpoint_path, methods in value.items():
                                if isinstance(methods, dict):
                                    for method in methods:
                                        if method.upper() in [
                                            "GET",
                                            "POST",
                                            "PUT",
                                            "DELETE",
                                            "PATCH",
                                        ]:
                                            endpoints.append(
                                                {"path": endpoint_path, "method": method.upper()}
                                            )
                    traverse(value, f"{path}/{key}")
            elif isinstance(obj, list):
                for item in obj:
                    traverse(item, path)

        traverse(data)
        return endpoints

    def _extract_configurations(self, data: Any) -> Dict[str, Any]:
        """Extract configuration values from JSON data."""
        configs = {}

        def traverse(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if key in ["config", "settings", "options", "params"]:
                        if isinstance(value, dict):
                            traverse(value, full_key)
                        else:
                            configs[full_key] = value
                    elif isinstance(value, (str, int, float, bool)):
                        if any(word in key.lower() for word in ["url", "host", "port", "timeout"]):
                            configs[full_key] = value

        traverse(data)
        return configs

    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction from text."""
        # Remove common words
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
        }

        words = re.findall(r"\b[a-z]+\b", text.lower())
        word_freq = {}

        for word in words:
            if word not in stopwords and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words]

    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate simple text summary."""
        # Take first paragraph or sentences
        sentences = re.split(r"[.!?]+", text)
        summary = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if len(summary) + len(sentence) < max_length:
                summary += sentence + ". "
            else:
                break

        if not summary:
            summary = text[:max_length] + "..."

        return summary.strip()

    async def batch_analyze(
        self, documents: List[Tuple[Union[str, Path], Optional[DocumentType]]], **kwargs
    ) -> List[DocumentAnalysis]:
        """
        Analyze multiple documents in parallel.

        Args:
            documents: List of (content, doc_type) tuples
            **kwargs: Additional parameters

        Returns:
            List of analysis results
        """
        tasks = [self.analyze(content, doc_type, **kwargs) for content, doc_type in documents]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch analysis failed for document {idx}: {result}")
                # Return empty analysis on error
                output.append(
                    DocumentAnalysis(
                        document_id=f"error_{idx}",
                        document_type=DocumentType.TEXT,
                        title=None,
                        summary=f"Analysis failed: {result}",
                        insights=[],
                        structure={},
                        metadata={"error": str(result)},
                    )
                )
            else:
                output.append(result)

        return output
