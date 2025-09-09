#!/usr/bin/env python3
"""
Enhanced Claude Format Adapter - Robust .jsonl parsing for SessionAnalyticsEngine
Addresses compatibility issues identified in Phase 1 testing and provides
seamless integration with the SessionAnalyticsEngine.
"""

import hashlib
import json
import re
import uuid as uuid_lib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple


@dataclass
class MessageNodeCompat:
    """Compatible MessageNode structure for SessionAnalyticsEngine"""

    uuid: str
    session_id: str
    parent_uuid: Optional[str]
    node_type: str  # 'user', 'assistant', 'system'
    timestamp: datetime
    content_hash: str
    token_count: int = 0
    raw_content: Any = None
    tool_calls: List = None
    tool_results: List = None

    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []
        if self.tool_results is None:
            self.tool_results = []


@dataclass
class ConversionStats:
    """Statistics from format conversion"""

    total_records: int
    converted_messages: int
    tool_calls_extracted: int
    tool_results_extracted: int
    errors_encountered: int
    size_reduction_percent: float
    conversion_time_seconds: float


@dataclass
class AdapterConfig:
    """Configuration for enhanced Claude format adapter"""

    preserve_all_metadata: bool = True
    extract_file_operations: bool = True
    consolidate_tool_sequences: bool = (
        False  # Keep False for SessionAnalyticsEngine compatibility
    )
    remove_duplicate_content: bool = False  # Keep False for accurate analytics
    max_content_length: int = 200000  # Increased for full content
    streaming_chunk_size: int = 1000
    generate_message_nodes: bool = True  # Generate MessageNode compatible objects


class EnhancedClaudeFormatAdapter:
    """
    Enhanced Claude .jsonl format adapter with full SessionAnalyticsEngine compatibility.
    Handles all Claude message types, tool calls, file operations, and system messages correctly.
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        self.config = config or AdapterConfig()

        # Claude message types mapping
        self.message_type_mapping = {
            "user": "user",
            "assistant": "assistant",
            "system": "system",
            "summary": "system",  # Map summary to system for analytics
        }

        # Tool categories for optimization (matching SessionAnalyticsEngine)
        self.tool_categories = {
            "file_ops": {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"},
            "shell_ops": {"Bash", "mcp__shell_exec__shell_exec", "Grep", "Glob"},
            "web_ops": {
                "WebSearch",
                "WebFetch",
                "mcp__web_search__brave_web_search",
                "mcp__web_search__brave_news_search",
                "mcp__firecrawl__firecrawl_scrape",
                "mcp__web_search__brave_local_search",
                "mcp__web_search__brave_video_search",
            },
            "knowledge": {
                "mcp__knowledge__knowledge_store",
                "mcp__knowledge__knowledge_query",
                "mcp__knowledge__knowledge_smart_query",
                "mcp__knowledge__knowledge_update",
                "mcp__knowledge__knowledge_delete",
                "mcp__knowledge__knowledge_supersede",
            },
            "planning": {"TodoWrite", "ExitPlanMode"},
            "agent": {"Task"},
            "thinking": {
                "mcp__thinking__metacognitivethinking",
                "mcp__thinking__getthinkinginsights",
            },
            "time": {
                "mcp__time__current_time",
                "mcp__time__relative_time",
                "mcp__time__convert_time",
                "mcp__time__days_in_month",
                "mcp__time__get_timestamp",
                "mcp__time__get_week_year",
            },
        }

    def parse_session_file(self, jsonl_path: Path) -> List[MessageNodeCompat]:
        """
        Parse Claude .jsonl session file into MessageNode compatible objects.
        This method provides direct compatibility with SessionAnalyticsEngine.

        Args:
            jsonl_path: Path to Claude .jsonl session file

        Returns:
            List of MessageNodeCompat objects ready for SessionAnalyticsEngine
        """
        nodes = []
        session_id = None

        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)

                        # Extract session ID from first valid record
                        if session_id is None:
                            session_id = self._extract_session_id(record, jsonl_path)

                        node = self._parse_record_to_node(record, session_id)
                        if node:
                            nodes.append(node)

                    except json.JSONDecodeError as e:
                        print(f"JSON decode error in {jsonl_path}:{line_num} - {e}")
                    except Exception as e:
                        print(
                            f"Record processing error in {jsonl_path}:{line_num} - {e}"
                        )

        except Exception as e:
            print(f"File read error {jsonl_path} - {e}")

        return nodes

    def convert_session_file(self, jsonl_path: Path) -> Dict[str, Any]:
        """
        Convert a Claude .jsonl session file to enhanced format with full analytics support.

        Args:
            jsonl_path: Path to Claude .jsonl session file

        Returns:
            Enhanced session data compatible with SessionAnalyticsEngine
        """
        start_time = datetime.now()

        # Initialize conversion tracking
        stats = ConversionStats(0, 0, 0, 0, 0, 0.0, 0.0)

        # Parse Claude session using enhanced parser
        nodes = self.parse_session_file(jsonl_path)

        # Build session metadata
        session_metadata = self._build_session_metadata(nodes, jsonl_path)

        # Calculate conversion statistics
        stats.converted_messages = len(nodes)
        stats.tool_calls_extracted = sum(len(node.tool_calls) for node in nodes)
        stats.tool_results_extracted = sum(len(node.tool_results) for node in nodes)

        end_time = datetime.now()
        stats.conversion_time_seconds = (end_time - start_time).total_seconds()

        # Build enhanced session structure
        enhanced_session = {
            "session_id": session_metadata.get("session_id", str(uuid_lib.uuid4())),
            "session_metadata": session_metadata,
            "message_nodes": nodes,  # Direct MessageNode compatibility
            "messages": [
                self._node_to_message_dict(node) for node in nodes
            ],  # Standard format
            "conversion_stats": {
                "total_records": stats.total_records,
                "converted_messages": stats.converted_messages,
                "tool_calls_extracted": stats.tool_calls_extracted,
                "tool_results_extracted": stats.tool_results_extracted,
                "errors_encountered": stats.errors_encountered,
                "conversion_time_seconds": round(stats.conversion_time_seconds, 2),
            },
            "analytics_ready": True,
            "enhancement_metadata": {
                "adapter_version": "2.0_enhanced",
                "conversion_timestamp": datetime.now().isoformat(),
                "source_file": str(jsonl_path),
                "sessionanalytics_compatible": True,
                "features_enabled": self._get_enabled_features(),
            },
        }

        return enhanced_session

    def _extract_session_id(self, record: Dict[str, Any], file_path: Path) -> str:
        """Extract session ID from record or file path"""
        # Try various session ID fields
        session_id = (
            record.get("sessionId") or record.get("session_id") or file_path.stem
        )

        return str(session_id)

    def _parse_record_to_node(
        self, record: Dict, session_id: str
    ) -> Optional[MessageNodeCompat]:
        """Parse individual JSONL record into MessageNodeCompat"""
        record_type = record.get("type")
        if not record_type:
            return None

        # Map Claude type to standard type
        node_type = self.message_type_mapping.get(record_type, record_type)

        # Parse timestamp
        timestamp = self._parse_timestamp(record.get("timestamp"))

        # Extract content and build hash
        raw_content = record.get("message", record)
        content_str = self._extract_content_string(record, record_type)
        content_hash = self._hash_content(content_str)

        # Create compatible node
        node = MessageNodeCompat(
            uuid=record.get("uuid", str(uuid_lib.uuid4())),
            session_id=session_id,
            parent_uuid=record.get("parentUuid"),
            node_type=node_type,
            timestamp=timestamp,
            content_hash=content_hash,
            raw_content=raw_content,
            token_count=self._estimate_tokens(record),
        )

        # Extract tool calls and results for assistant messages
        if record_type == "assistant":
            tool_calls, tool_results = self._extract_tool_usage(record)
            node.tool_calls = tool_calls
            node.tool_results = tool_results

        return node

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime with robust handling - always returns timezone-naive"""
        if not timestamp_str:
            return datetime.now()

        try:
            # Handle ISO format with/without timezone
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"

            # Try fromisoformat first
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            # Convert to naive datetime for compatibility
            return dt.replace(tzinfo=None) if dt.tzinfo else dt
        except (ValueError, AttributeError):
            try:
                # Try parsing common formats
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%d %H:%M:%S",
                ]:
                    try:
                        return datetime.strptime(
                            timestamp_str.replace("Z", ""), fmt.replace("Z", "")
                        )
                    except ValueError:
                        continue
            except:
                pass

        # Fallback to current time
        return datetime.now()

    def _hash_content(self, content: str) -> str:
        """Generate SHA256 hash for content deduplication"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _extract_content_string(self, record: Dict[str, Any], record_type: str) -> str:
        """Extract content string from record based on type"""
        message_data = record.get("message", {})

        if record_type == "user":
            return self._extract_user_content(record)
        elif record_type == "assistant":
            return self._extract_assistant_content(record)
        elif record_type == "system":
            return self._extract_system_content(record)
        elif record_type == "summary":
            return record.get("summary", str(message_data))
        else:
            return str(message_data)

    def _extract_user_content(self, record: Dict[str, Any]) -> str:
        """Extract user message content"""
        message_data = record.get("message", {})

        if isinstance(message_data, dict):
            content = message_data.get("content", "")
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Handle structured content
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif "content" in item:
                            text_parts.append(str(item["content"]))
                    else:
                        text_parts.append(str(item))
                return " ".join(text_parts)

        return str(message_data)

    def _extract_assistant_content(self, record: Dict[str, Any]) -> str:
        """Extract assistant message content, separating text from tool usage"""
        message_data = record.get("message", {})

        if isinstance(message_data, dict):
            content = message_data.get("content", "")

            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Extract only text content, tools handled separately
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        # Skip tool_use and tool_result - handled in _extract_tool_usage

                return " ".join(text_parts)

        return str(message_data)

    def _extract_system_content(self, record: Dict[str, Any]) -> str:
        """Extract system message content"""
        message_data = record.get("message", {})
        if isinstance(message_data, dict):
            return str(message_data.get("content", ""))
        return str(message_data)

    def _extract_tool_usage(
        self, record: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Extract tool calls and results from assistant message"""
        tool_calls = []
        tool_results = []

        message_data = record.get("message", {})
        content = message_data.get("content", [])

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "tool_use":
                        tool_call = {
                            "id": item.get("id", str(uuid_lib.uuid4())),
                            "name": item.get("name", "unknown"),
                            "input": item.get("input", {}),
                            "category": self._categorize_tool(item.get("name", "")),
                        }
                        tool_calls.append(tool_call)

                    elif item.get("type") == "tool_result":
                        tool_result = {
                            "tool_use_id": item.get("tool_use_id"),
                            "is_error": item.get("is_error", False),
                            "content": self._truncate_tool_result(
                                item.get("content", "")
                            ),
                        }
                        tool_results.append(tool_result)

        # Also check for toolUseResult in user messages
        if "toolUseResult" in record:
            tool_result_data = record["toolUseResult"]
            tool_result = {
                "tool_use_id": "user_result",
                "is_error": False,
                "content": str(tool_result_data),
            }
            tool_results.append(tool_result)

        return tool_calls, tool_results

    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool by name for optimization"""
        for category, tools in self.tool_categories.items():
            if tool_name in tools:
                return category

        if tool_name.startswith("mcp__"):
            return "mcp_tools"

        return "other"

    def _truncate_tool_result(self, content: Any) -> str:
        """Truncate large tool results for optimization"""
        content_str = str(content)

        # Apply content length limit
        if len(content_str) > self.config.max_content_length:
            truncated = content_str[: self.config.max_content_length]
            return truncated + f"... [truncated from {len(content_str)} chars]"

        return content_str

    def _estimate_tokens(self, record: Dict) -> int:
        """Rough token count estimation (1 token ≈ 4 characters)"""
        content_str = json.dumps(record, ensure_ascii=False)
        return max(1, len(content_str) // 4)

    def _build_session_metadata(
        self, nodes: List[MessageNodeCompat], file_path: Path
    ) -> Dict[str, Any]:
        """Build comprehensive session metadata"""
        if not nodes:
            return {"session_id": file_path.stem, "source_file": str(file_path)}

        session_id = nodes[0].session_id
        timestamps = [node.timestamp for node in nodes if node.timestamp]

        # Ensure all timestamps are timezone-naive for comparison
        naive_timestamps = []
        for ts in timestamps:
            if ts.tzinfo is not None:
                naive_timestamps.append(ts.replace(tzinfo=None))
            else:
                naive_timestamps.append(ts)

        metadata = {
            "session_id": session_id,
            "source_file": str(file_path),
            "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "created_at": min(naive_timestamps) if naive_timestamps else datetime.now(),
            "ended_at": max(naive_timestamps) if naive_timestamps else datetime.now(),
            "message_count": len(nodes),
            "tool_usage_count": sum(len(node.tool_calls) for node in nodes),
            "conversion_timestamp": datetime.now().isoformat(),
        }

        # Extract project context from file path
        if "master_root" in str(file_path):
            try:
                path_parts = str(file_path).split("master_root")
                if len(path_parts) > 1:
                    project_path = (
                        path_parts[1].split("/")[1]
                        if "/" in path_parts[1]
                        else "unknown"
                    )
                    metadata["project_context"] = project_path
            except:
                pass

        return metadata

    def _node_to_message_dict(self, node: MessageNodeCompat) -> Dict[str, Any]:
        """Convert MessageNodeCompat to dictionary format"""
        return {
            "uuid": node.uuid,
            "type": node.node_type,
            "timestamp": node.timestamp.isoformat(),
            "parent_uuid": node.parent_uuid,
            "content": self._extract_content_string_from_raw(
                node.raw_content, node.node_type
            ),
            "content_hash": node.content_hash,
            "token_count": node.token_count,
            "tool_calls": node.tool_calls,
            "tool_results": node.tool_results,
        }

    def _extract_content_string_from_raw(self, raw_content: Any, node_type: str) -> str:
        """Extract content string from raw content"""
        if isinstance(raw_content, dict):
            content = raw_content.get("content", "")
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)

        return str(raw_content)

    def _get_enabled_features(self) -> List[str]:
        """Get list of enabled features"""
        features = [
            "enhanced_claude_parsing",
            "messagenode_compatibility",
            "comprehensive_tool_extraction",
            "robust_timestamp_parsing",
            "sessionanalytics_integration",
        ]

        if self.config.extract_file_operations:
            features.append("file_operation_tracking")

        if self.config.preserve_all_metadata:
            features.append("metadata_preservation")

        return features

    def create_sessionanalytics_compatible_parser(self):
        """Create a parser that can replace the LogParser in SessionAnalyticsEngine"""

        class CompatibleLogParser:
            def __init__(self, adapter):
                self.adapter = adapter
                self.tool_patterns = adapter.tool_categories

            def parse_session_file(self, jsonl_path: Path) -> List:
                """Parse session file returning MessageNode compatible objects"""
                return self.adapter.parse_session_file(jsonl_path)

            def _parse_record(self, record: Dict, session_id: str):
                """Parse individual record"""
                return self.adapter._parse_record_to_node(record, session_id)

        return CompatibleLogParser(self)

    def streaming_parse(
        self, jsonl_path: Path
    ) -> Generator[MessageNodeCompat, None, None]:
        """Stream parse large files yielding MessageNode objects one at a time"""
        session_id = None

        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)

                    if session_id is None:
                        session_id = self._extract_session_id(record, jsonl_path)

                    node = self._parse_record_to_node(record, session_id)
                    if node:
                        yield node

                except Exception as e:
                    print(f"Streaming parse error at line {line_num}: {e}")
                    continue


def create_enhanced_session_analytics_engine(
    claude_adapter: Optional[EnhancedClaudeFormatAdapter] = None,
):
    """
    Create a SessionAnalyticsEngine with enhanced Claude format support.
    This replaces the standard LogParser with the enhanced adapter.
    """
    from session_analytics_engine import (
        ConversationAnalyzer,
        FileAnalyzer,
        SessionAnalyticsEngine,
        SessionMetrics,
        ToolAnalyzer,
    )

    if claude_adapter is None:
        claude_adapter = EnhancedClaudeFormatAdapter()

    # Create enhanced analytics engine
    enhanced_engine = SessionAnalyticsEngine()

    # Replace the log parser with our enhanced adapter
    enhanced_engine.log_parser = (
        claude_adapter.create_sessionanalytics_compatible_parser()
    )

    return enhanced_engine


# Usage examples
if __name__ == "__main__":
    print("Enhanced Claude Format Adapter - Direct Usage")

    # Example 1: Direct parsing to MessageNode objects
    adapter = EnhancedClaudeFormatAdapter()
    claude_projects = Path("/home/opsvi/.claude/projects")
    sample_files = list(claude_projects.glob("**/*.jsonl"))[:1]

    if sample_files:
        sample_file = sample_files[0]
        print(f"Testing with: {sample_file.name}")

        # Parse to MessageNode objects
        nodes = adapter.parse_session_file(sample_file)
        print(f"Parsed {len(nodes)} message nodes")

        # Convert to enhanced format
        enhanced_session = adapter.convert_session_file(sample_file)
        print(f"Enhanced session: {enhanced_session['session_id']}")
        print(f"Analytics ready: {enhanced_session['analytics_ready']}")

        # Create enhanced analytics engine
        enhanced_engine = create_enhanced_session_analytics_engine(adapter)
        print("Enhanced SessionAnalyticsEngine created successfully!")
