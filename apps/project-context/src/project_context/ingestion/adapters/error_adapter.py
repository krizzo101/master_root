"""Error and diagnostic data adapter."""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import structlog

from ...models.common import ContextItem
from ..base_adapter import AdapterConfig, BaseAdapter, BatchMode
from ..transformers import DataTransformer

logger = structlog.get_logger(__name__)


class ErrorAdapter(BaseAdapter):
    """Adapter for ingesting error and diagnostic data.

    Supports:
    - Application error logs
    - IDE diagnostics and warnings
    - Stack traces and exception data
    - Performance issues
    - Test failures
    """

    @classmethod
    def default_config(cls) -> AdapterConfig:
        """Get default configuration for error adapter."""
        return AdapterConfig(
            adapter_id="error",
            source_type="error",
            batch_mode=BatchMode.STREAMING,
            batch_size=100,
            generate_embeddings=True,
            generate_summaries=False,
            extract_relationships=True,
            source_config={
                "input_sources": ["logs", "ide", "test", "monitor"],
                "log_file_patterns": ["*.log", "error*.log", "*.err"],
                "log_directories": ["./logs", "./log"],
                "ide_diagnostic_formats": ["lsp", "eslint", "pylint"],
                "severity_filters": ["error", "warning"],  # empty = all
                "stack_trace_parsing": True,
                "extract_file_locations": True,
                "group_similar_errors": True,
                "similarity_threshold": 0.8,
                "max_error_age_days": 30,
                "exclude_patterns": [
                    r".*DEBUG.*",
                    r".*INFO.*",
                    r".*connection.*timeout.*",  # Common noise
                ],
            },
        )

    def __init__(self, config: AdapterConfig):
        """Initialize error adapter."""
        super().__init__(config)
        self.transformer = DataTransformer()
        self._processed_logs: set = set()
        self._error_groups: Dict[str, List[Dict[str, Any]]] = {}

    async def initialize(self) -> None:
        """Initialize error adapter resources."""
        self.logger.info("Initializing error adapter")

        # Validate input sources
        input_sources = self.config.source_config.get("input_sources", [])
        valid_sources = ["logs", "ide", "test", "monitor", "api"]

        for source in input_sources:
            if source not in valid_sources:
                self.logger.warning(f"Unknown input source: {source}")

        # Check log directories
        log_dirs = self.config.source_config.get("log_directories", [])
        for log_dir in log_dirs:
            if not Path(log_dir).exists():
                self.logger.warning(f"Log directory does not exist: {log_dir}")

        self.logger.info("Error adapter initialized")

    async def fetch_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch error and diagnostic items."""
        input_sources = self.config.source_config.get("input_sources", ["logs"])

        count = 0

        for source in input_sources:
            if limit and count >= limit:
                break

            if source == "logs":
                async for item in self._fetch_from_logs(since, until, limit - count):
                    yield item
                    count += 1
            elif source == "ide":
                async for item in self._fetch_from_ide(since, until, limit - count):
                    yield item
                    count += 1
            elif source == "test":
                async for item in self._fetch_from_test_results(
                    since, until, limit - count
                ):
                    yield item
                    count += 1
            elif source == "monitor":
                async for item in self._fetch_from_monitoring(
                    since, until, limit - count
                ):
                    yield item
                    count += 1

    async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform raw error item into ContextItem."""
        # Create base context item
        source_id = (
            raw_item.get("error_id")
            or raw_item.get("id")
            or self._generate_error_id(raw_item)
        )

        item = self.transformer.create_base_context_item(
            source_type="error", source_id=source_id, raw_data=raw_item
        )

        # Error-specific fields
        item.title = self._extract_error_title(raw_item)
        item.content = self._extract_error_content(raw_item)

        # Parse severity
        item.severity = self._parse_severity(
            raw_item.get("severity") or raw_item.get("level", "error")
        )

        # Extract location information
        location_info = self._extract_location_info(raw_item)
        if location_info:
            item.file_path = location_info.get("file_path")
            item.line_start = location_info.get("line_number")
            item.function_name = location_info.get("function_name")
            item.class_name = location_info.get("class_name")

        # Error metadata
        error_metadata = {
            "error_type": raw_item.get("error_type") or raw_item.get("exception_type"),
            "error_code": raw_item.get("error_code") or raw_item.get("code"),
            "source": raw_item.get("source", "unknown"),
            "category": self._categorize_error(raw_item),
            "stack_trace": raw_item.get("stack_trace") or raw_item.get("traceback"),
            "context": raw_item.get("context", {}),
        }

        # Extract additional metadata based on source
        source = raw_item.get("source", "")
        if source == "ide":
            error_metadata.update(
                {
                    "rule": raw_item.get("rule"),
                    "rule_id": raw_item.get("rule_id"),
                    "fix_suggestion": raw_item.get("fix_suggestion"),
                }
            )
        elif source == "test":
            error_metadata.update(
                {
                    "test_name": raw_item.get("test_name"),
                    "test_file": raw_item.get("test_file"),
                    "test_framework": raw_item.get("test_framework"),
                    "assertion": raw_item.get("assertion"),
                }
            )
        elif source == "monitor":
            error_metadata.update(
                {
                    "metric_name": raw_item.get("metric_name"),
                    "threshold": raw_item.get("threshold"),
                    "actual_value": raw_item.get("actual_value"),
                    "alert_id": raw_item.get("alert_id"),
                }
            )

        item.metrics = error_metadata

        # Set entity type
        item.entity_type = self._determine_entity_type(raw_item)

        # Add tags based on error characteristics
        tags = ["error"]
        tags.append(item.severity)

        if error_metadata.get("category"):
            tags.append(error_metadata["category"])

        if error_metadata.get("source"):
            tags.append(f"source_{error_metadata['source']}")

        # Language/technology tags
        if item.file_path:
            extension = Path(item.file_path).suffix.lower()
            if extension:
                tags.append(f"lang_{extension[1:]}")  # Remove the dot

        item.tags = tags

        # Apply transformations
        item = await self.transformer.transform_item(item)

        return item

    async def detect_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships with other error items."""
        relationships = []

        if not item.metrics:
            return relationships

        # Similar error relationships
        for context_item in context_window:
            if context_item.source_type != "error" or not context_item.metrics:
                continue

            similarity = self._calculate_error_similarity(item, context_item)
            if similarity > self.config.source_config.get("similarity_threshold", 0.8):
                relationships.append(("similar_error", context_item.id, similarity))

        # File location relationships
        if item.file_path:
            for context_item in context_window:
                if (
                    context_item.file_path == item.file_path
                    and context_item.id != item.id
                ):
                    relationships.append(("same_file", context_item.id, 0.7))

        # Stack trace relationships
        item_stack = item.metrics.get("stack_trace", "")
        if item_stack:
            for context_item in context_window:
                if not context_item.metrics:
                    continue

                context_stack = context_item.metrics.get("stack_trace", "")
                if context_stack and self._stacks_related(item_stack, context_stack):
                    relationships.append(("related_stack_trace", context_item.id, 0.6))

        # Error chain relationships (caused by)
        if "caused by" in item.content.lower():
            # Look for referenced error IDs or stack traces
            for context_item in context_window:
                if self._is_causal_relationship(item, context_item):
                    relationships.append(("caused_by", context_item.id, 0.8))

        return relationships

    async def cleanup(self) -> None:
        """Clean up error adapter resources."""
        self.logger.info("Cleaning up error adapter")
        self._processed_logs.clear()
        self._error_groups.clear()

    # Private methods

    async def _fetch_from_logs(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch errors from log files."""
        log_dirs = self.config.source_config.get("log_directories", ["./logs"])
        patterns = self.config.source_config.get("log_file_patterns", ["*.log"])

        count = 0

        for log_dir in log_dirs:
            dir_path = Path(log_dir)
            if not dir_path.exists():
                continue

            for pattern in patterns:
                for log_file in dir_path.glob(pattern):
                    if str(log_file) in self._processed_logs:
                        continue

                    async for error in self._parse_log_file(log_file, since, until):
                        if limit and count >= limit:
                            return

                        error["source"] = "logs"
                        yield error
                        count += 1

                    self._processed_logs.add(str(log_file))

    async def _parse_log_file(
        self,
        log_file: Path,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Parse errors from a log file."""
        exclude_patterns = self.config.source_config.get("exclude_patterns", [])
        severity_filters = self.config.source_config.get("severity_filters", [])

        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                current_error = None
                stack_trace_lines = []

                for line_num, line in enumerate(f, 1):
                    line = line.rstrip()

                    # Skip empty lines
                    if not line:
                        continue

                    # Check exclusion patterns
                    if any(re.search(pattern, line) for pattern in exclude_patterns):
                        continue

                    # Parse log line
                    parsed_line = self._parse_log_line(line)
                    if not parsed_line:
                        # Might be continuation of stack trace
                        if current_error and self._is_stack_trace_line(line):
                            stack_trace_lines.append(line)
                        continue

                    # Check severity filter
                    if (
                        severity_filters
                        and parsed_line.get("severity") not in severity_filters
                    ):
                        continue

                    # Check timestamp filter
                    if since or until:
                        log_time = parsed_line.get("timestamp")
                        if log_time:
                            if since and log_time < since:
                                continue
                            if until and log_time > until:
                                continue

                    # If we have a current error, finalize it
                    if current_error:
                        if stack_trace_lines:
                            current_error["stack_trace"] = "\n".join(stack_trace_lines)

                        yield current_error
                        stack_trace_lines = []

                    # Start new error
                    current_error = {
                        **parsed_line,
                        "file": str(log_file),
                        "line_number": line_num,
                        "raw_line": line,
                    }

                # Yield the last error if any
                if current_error:
                    if stack_trace_lines:
                        current_error["stack_trace"] = "\n".join(stack_trace_lines)
                    yield current_error

        except Exception as e:
            self.logger.error(f"Error parsing log file: {log_file}", error=str(e))

    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line."""
        # Common log patterns
        patterns = [
            # Standard format: timestamp LEVEL message
            r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[^\s]*)\s+(?P<severity>\w+)\s+(?P<message>.*)",
            # Syslog format
            r"(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+\w+\s+(?P<severity>\w+):\s+(?P<message>.*)",
            # JSON format
            r'^\{.*"level":\s*"(?P<severity>\w+)".*"message":\s*"(?P<message>.*?)".*\}$',
            # Simple format: LEVEL: message
            r"^(?P<severity>ERROR|WARN|WARNING|INFO|DEBUG):\s*(?P<message>.*)",
        ]

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                result = match.groupdict()

                # Parse timestamp if present
                if "timestamp" in result:
                    try:
                        # Try different timestamp formats
                        timestamp_str = result["timestamp"]
                        result["timestamp"] = self._parse_timestamp(timestamp_str)
                    except (ValueError, TypeError):
                        result["timestamp"] = None

                # Normalize severity
                if "severity" in result:
                    result["severity"] = self._normalize_severity(result["severity"])

                return result

        return None

    def _is_stack_trace_line(self, line: str) -> bool:
        """Check if line is part of a stack trace."""
        stack_trace_indicators = [
            r"^\s+at\s+",  # Java/JavaScript stack traces
            r'^\s+File\s+".*",\s+line\s+\d+',  # Python stack traces
            r"^\s+in\s+.*:\d+",  # Various formats
            r"^\s+.*\(\s*.*:\d+\s*\)",  # Function calls with line numbers
            r"^\s*Traceback\s*\(most recent call last\)",  # Python traceback
            r"^\s*Exception\s+in\s+thread",  # Java exceptions
            r"^\s*Caused by:",  # Exception chains
        ]

        return any(re.search(pattern, line) for pattern in stack_trace_indicators)

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse various timestamp formats."""
        # Common timestamp formats
        formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%b %d %H:%M:%S",  # Syslog format
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        return None

    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity levels."""
        severity = severity.upper()

        if severity in ["ERROR", "ERR", "FATAL", "CRITICAL"]:
            return "error"
        elif severity in ["WARN", "WARNING"]:
            return "warning"
        elif severity in ["INFO", "INFORMATION"]:
            return "info"
        elif severity in ["DEBUG", "TRACE"]:
            return "debug"
        else:
            return "unknown"

    async def _fetch_from_ide(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from IDE diagnostics (placeholder)."""
        # This would integrate with LSP servers, ESLint, PyLint, etc.
        self.logger.info("IDE diagnostic fetching not yet implemented")
        return
        yield  # Make this a generator

    async def _fetch_from_test_results(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from test failure reports (placeholder)."""
        # This would parse JUnit XML, pytest reports, etc.
        self.logger.info("Test result fetching not yet implemented")
        return
        yield  # Make this a generator

    async def _fetch_from_monitoring(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from monitoring alerts (placeholder)."""
        # This would integrate with monitoring systems
        self.logger.info("Monitoring alert fetching not yet implemented")
        return
        yield  # Make this a generator

    def _extract_error_title(self, raw_error: Dict[str, Any]) -> str:
        """Extract a concise title from error data."""
        # Try different title sources
        title_candidates = [
            raw_error.get("title"),
            raw_error.get("summary"),
            raw_error.get("error_type"),
            raw_error.get("exception_type"),
        ]

        for candidate in title_candidates:
            if candidate:
                return str(candidate)[:200]  # Limit length

        # Fall back to first line of message
        message = raw_error.get("message", "")
        if message:
            first_line = message.split("\n")[0].strip()
            return first_line[:200] if first_line else "Unknown Error"

        return "Unknown Error"

    def _extract_error_content(self, raw_error: Dict[str, Any]) -> str:
        """Extract comprehensive error content."""
        parts = []

        # Main message
        message = raw_error.get("message", "")
        if message:
            parts.append(message)

        # Stack trace
        stack_trace = raw_error.get("stack_trace", "")
        if stack_trace:
            parts.append("Stack trace:")
            parts.append(stack_trace)

        # Context information
        context = raw_error.get("context", {})
        if context:
            parts.append("Context:")
            for key, value in context.items():
                parts.append(f"  {key}: {value}")

        # Additional details based on source
        source = raw_error.get("source", "")
        if source == "ide":
            rule = raw_error.get("rule")
            if rule:
                parts.append(f"Rule: {rule}")

            fix_suggestion = raw_error.get("fix_suggestion")
            if fix_suggestion:
                parts.append(f"Suggested fix: {fix_suggestion}")

        return "\n".join(parts)

    def _extract_location_info(
        self, raw_error: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract file location information from error."""
        location = {}

        # Direct file path
        if raw_error.get("file_path"):
            location["file_path"] = raw_error["file_path"]
        elif raw_error.get("file"):
            location["file_path"] = raw_error["file"]

        # Line number
        if raw_error.get("line_number"):
            location["line_number"] = raw_error["line_number"]
        elif raw_error.get("line"):
            location["line_number"] = raw_error["line"]

        # Function/class information
        location["function_name"] = raw_error.get("function_name")
        location["class_name"] = raw_error.get("class_name")

        # Try to extract from stack trace
        stack_trace = raw_error.get("stack_trace", "")
        if stack_trace and not location.get("file_path"):
            extracted = self._extract_location_from_stack_trace(stack_trace)
            location.update(extracted)

        return location if any(location.values()) else None

    def _extract_location_from_stack_trace(self, stack_trace: str) -> Dict[str, Any]:
        """Extract location information from stack trace."""
        location = {}

        # Python stack trace pattern
        python_pattern = r'File "([^"]+)", line (\d+), in (.+)'
        match = re.search(python_pattern, stack_trace)
        if match:
            location["file_path"] = match.group(1)
            location["line_number"] = int(match.group(2))
            location["function_name"] = match.group(3)

        # Java stack trace pattern
        java_pattern = r"at (.+)\.(.+)\((.+):(\d+)\)"
        match = re.search(java_pattern, stack_trace)
        if match:
            location["class_name"] = match.group(1)
            location["function_name"] = match.group(2)
            location["file_path"] = match.group(3)
            location["line_number"] = int(match.group(4))

        return location

    def _categorize_error(self, raw_error: Dict[str, Any]) -> str:
        """Categorize error based on content."""
        message = raw_error.get("message", "").lower()
        error_type = (raw_error.get("error_type") or "").lower()

        # Network errors
        if any(
            term in message
            for term in ["connection", "network", "timeout", "unreachable"]
        ):
            return "network"

        # File system errors
        if any(
            term in message
            for term in ["file not found", "permission denied", "disk", "directory"]
        ):
            return "filesystem"

        # Memory errors
        if any(
            term in message
            for term in ["out of memory", "memory", "heap", "stack overflow"]
        ):
            return "memory"

        # Syntax errors
        if any(
            term in message
            for term in ["syntax error", "parse error", "invalid syntax"]
        ):
            return "syntax"

        # Type errors
        if any(
            term in message for term in ["type error", "attribute error", "undefined"]
        ):
            return "type"

        # Database errors
        if any(term in message for term in ["database", "sql", "connection", "query"]):
            return "database"

        # Authentication/authorization errors
        if any(
            term in message
            for term in ["unauthorized", "forbidden", "authentication", "permission"]
        ):
            return "auth"

        return "unknown"

    def _determine_entity_type(self, raw_error: Dict[str, Any]) -> str:
        """Determine entity type based on error characteristics."""
        source = raw_error.get("source", "")

        if source == "test":
            return "test_failure"
        elif source == "ide":
            return "diagnostic"
        elif source == "monitor":
            return "alert"
        else:
            severity = raw_error.get("severity", "error")
            if severity == "error":
                return "error"
            elif severity == "warning":
                return "warning"
            else:
                return "diagnostic"

    def _parse_severity(self, severity: str) -> str:
        """Parse and normalize severity level."""
        if not severity:
            return "medium"

        severity = severity.lower()

        if severity in ["critical", "fatal", "high"]:
            return "high"
        elif severity in ["error", "err"]:
            return "high"
        elif severity in ["warning", "warn", "medium"]:
            return "medium"
        elif severity in ["info", "information", "low"]:
            return "low"
        elif severity in ["debug", "trace"]:
            return "low"
        else:
            return "medium"

    def _generate_error_id(self, raw_error: Dict[str, Any]) -> str:
        """Generate a unique ID for an error."""
        # Create hash based on error characteristics
        content = f"{raw_error.get('message', '')}{raw_error.get('file_path', '')}{raw_error.get('line_number', '')}"
        return f"error_{hash(content) % 1000000:06d}"

    def _calculate_error_similarity(
        self, error1: ContextItem, error2: ContextItem
    ) -> float:
        """Calculate similarity between two errors."""
        if not error1.metrics or not error2.metrics:
            return 0.0

        similarity_score = 0.0

        # Error type similarity
        type1 = error1.metrics.get("error_type", "")
        type2 = error2.metrics.get("error_type", "")
        if type1 and type2 and type1 == type2:
            similarity_score += 0.3

        # Message similarity (simple word overlap)
        message1_words = set(error1.content.lower().split())
        message2_words = set(error2.content.lower().split())
        if message1_words and message2_words:
            overlap = len(message1_words & message2_words)
            union = len(message1_words | message2_words)
            similarity_score += 0.4 * (overlap / union) if union > 0 else 0

        # Location similarity
        if error1.file_path and error2.file_path:
            if error1.file_path == error2.file_path:
                similarity_score += 0.2

                # Line proximity bonus
                if error1.line_start and error2.line_start:
                    line_diff = abs(error1.line_start - error2.line_start)
                    if line_diff <= 5:  # Within 5 lines
                        similarity_score += 0.1

        # Category similarity
        cat1 = error1.metrics.get("category", "")
        cat2 = error2.metrics.get("category", "")
        if cat1 and cat2 and cat1 == cat2:
            similarity_score += 0.1

        return min(1.0, similarity_score)

    def _stacks_related(self, stack1: str, stack2: str) -> bool:
        """Check if two stack traces are related."""
        # Simple check for common function calls
        stack1_functions = re.findall(r"at (.+?)\(", stack1)
        stack2_functions = re.findall(r"at (.+?)\(", stack2)

        if not stack1_functions or not stack2_functions:
            return False

        # Check for overlap in function calls
        overlap = len(set(stack1_functions) & set(stack2_functions))
        return overlap >= 2  # At least 2 common functions

    def _is_causal_relationship(self, error1: ContextItem, error2: ContextItem) -> bool:
        """Check if error1 was caused by error2."""
        # Look for references to error2 in error1's content
        if error2.source_id in error1.content:
            return True

        # Check timestamp ordering (error2 should be earlier)
        if error2.timestamp and error1.timestamp:
            time_diff = (error1.timestamp - error2.timestamp).total_seconds()
            return 0 <= time_diff <= 300  # Within 5 minutes

        return False
