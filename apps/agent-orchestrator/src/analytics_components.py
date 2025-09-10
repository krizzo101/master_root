#!/usr/bin/env python3
"""
Modular Analytics Components for Session Analysis
Provides reusable components for extending session analytics capabilities.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


class AnalyticsComponent(ABC):
    """Base class for all analytics components"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def analyze(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze session data and return results"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return the schema for this component's output"""
        pass


class SessionMetricsExtractor(AnalyticsComponent):
    """Extracts basic session metrics"""

    def __init__(self):
        super().__init__("SessionMetricsExtractor")

    def analyze(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic session metrics"""
        records = session_data.get("records", [])
        metadata = session_data.get("metadata", {})

        # Extract timestamps
        timestamps = []
        for record in records:
            ts = record.get("timestamp")
            if ts:
                try:
                    timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                except (ValueError, TypeError):
                    continue

        start_time = min(timestamps) if timestamps else datetime.now()
        end_time = max(timestamps) if timestamps else datetime.now()
        duration = (end_time - start_time).total_seconds() / 60.0

        # Count record types
        record_types = {}
        for record in records:
            record_type = record.get("type", "unknown")
            record_types[record_type] = record_types.get(record_type, 0) + 1

        return {
            "session_id": metadata.get("session_id", "unknown"),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": duration,
            "total_records": len(records),
            "record_types": record_types,
            "working_directory": metadata.get("cwd", ""),
            "git_branch": metadata.get("git_branch", ""),
            "claude_version": metadata.get("version", ""),
        }

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "start_time": {"type": "string", "format": "date-time"},
                "end_time": {"type": "string", "format": "date-time"},
                "duration_minutes": {"type": "number"},
                "total_records": {"type": "integer"},
                "record_types": {"type": "object"},
                "working_directory": {"type": "string"},
                "git_branch": {"type": "string"},
                "claude_version": {"type": "string"},
            },
        }


class ToolUsageExtractor(AnalyticsComponent):
    """Extracts tool usage analytics"""

    def __init__(self):
        super().__init__("ToolUsageExtractor")

    def analyze(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tool usage analytics"""
        records = session_data.get("records", [])
        tool_calls = []
        tool_results = {}

        # Extract tool calls and results
        for record in records:
            if record.get("type") == "assistant":
                content = record.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_use":
                            tool_calls.append(
                                {
                                    "id": item.get("id"),
                                    "name": item.get("name"),
                                    "input": item.get("input", {}),
                                    "timestamp": record.get("timestamp"),
                                }
                            )

            elif record.get("type") == "user":
                content = record.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_result":
                            tool_use_id = item.get("tool_use_id")
                            tool_results[tool_use_id] = {
                                "is_error": item.get("is_error", False),
                                "content": str(item.get("content", "")),
                                "timestamp": record.get("timestamp"),
                            }

        # Aggregate by tool name
        tool_stats = {}
        for call in tool_calls:
            tool_name = call["name"]
            if tool_name not in tool_stats:
                tool_stats[tool_name] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "unique_parameters": set(),
                    "call_timestamps": [],
                }

            tool_stats[tool_name]["total_calls"] += 1
            tool_stats[tool_name]["call_timestamps"].append(call["timestamp"])

            # Check if call was successful
            result = tool_results.get(call["id"], {})
            if result.get("is_error", False):
                tool_stats[tool_name]["failed_calls"] += 1
            else:
                tool_stats[tool_name]["successful_calls"] += 1

            # Track parameter patterns
            for param_key in call["input"].keys():
                tool_stats[tool_name]["unique_parameters"].add(param_key)

        # Convert sets to lists for JSON serialization
        for tool_name, stats in tool_stats.items():
            stats["unique_parameters"] = list(stats["unique_parameters"])
            stats["success_rate"] = (
                stats["successful_calls"] / stats["total_calls"]
                if stats["total_calls"] > 0
                else 0
            )

        return {
            "total_tool_calls": len(tool_calls),
            "unique_tools": len(tool_stats),
            "tool_statistics": tool_stats,
        }

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "total_tool_calls": {"type": "integer"},
                "unique_tools": {"type": "integer"},
                "tool_statistics": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "total_calls": {"type": "integer"},
                            "successful_calls": {"type": "integer"},
                            "failed_calls": {"type": "integer"},
                            "success_rate": {"type": "number"},
                            "unique_parameters": {"type": "array"},
                            "call_timestamps": {"type": "array"},
                        },
                    },
                },
            },
        }


class FileActivityExtractor(AnalyticsComponent):
    """Extracts file activity analytics"""

    def __init__(self):
        super().__init__("FileActivityExtractor")
        self.file_tools = {"Read", "Write", "Edit", "MultiEdit", "Bash", "Glob", "Grep"}

    def analyze(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract file activity analytics"""
        records = session_data.get("records", [])
        file_operations = []

        for record in records:
            if record.get("type") == "assistant":
                content = record.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name")
                            tool_input = item.get("input", {})

                            if tool_name in self.file_tools:
                                file_paths = self._extract_file_paths(
                                    tool_name, tool_input
                                )

                                for file_path in file_paths:
                                    file_operations.append(
                                        {
                                            "file_path": file_path,
                                            "operation": self._get_operation_type(
                                                tool_name
                                            ),
                                            "tool_name": tool_name,
                                            "timestamp": record.get("timestamp"),
                                            "tool_input": tool_input,
                                        }
                                    )

        # Aggregate by file
        file_stats = {}
        for op in file_operations:
            file_path = op["file_path"]
            if file_path not in file_stats:
                file_stats[file_path] = {
                    "total_operations": 0,
                    "operation_types": set(),
                    "tools_used": set(),
                    "first_access": None,
                    "last_access": None,
                    "access_pattern": [],
                }

            stats = file_stats[file_path]
            stats["total_operations"] += 1
            stats["operation_types"].add(op["operation"])
            stats["tools_used"].add(op["tool_name"])
            stats["access_pattern"].append(
                {"timestamp": op["timestamp"], "operation": op["operation"]}
            )

            # Update first/last access times
            timestamp = op["timestamp"]
            if stats["first_access"] is None or timestamp < stats["first_access"]:
                stats["first_access"] = timestamp
            if stats["last_access"] is None or timestamp > stats["last_access"]:
                stats["last_access"] = timestamp

        # Convert sets to lists for JSON serialization
        for file_path, stats in file_stats.items():
            stats["operation_types"] = list(stats["operation_types"])
            stats["tools_used"] = list(stats["tools_used"])

        return {
            "total_file_operations": len(file_operations),
            "unique_files_accessed": len(file_stats),
            "file_statistics": file_stats,
            "file_type_distribution": self._get_file_type_distribution(
                file_stats.keys()
            ),
        }

    def _extract_file_paths(self, tool_name: str, tool_input: Dict) -> List[str]:
        """Extract file paths from tool input"""
        file_paths = []

        # Direct file path parameters
        if "file_path" in tool_input:
            file_paths.append(tool_input["file_path"])
        elif "path" in tool_input:
            file_paths.append(tool_input["path"])

        # For Bash commands, try to extract file paths
        elif tool_name == "Bash" and "command" in tool_input:
            command = tool_input["command"]
            # Simple heuristic: look for file-like arguments
            parts = command.split()
            for part in parts:
                if (
                    "/" in part
                    and not part.startswith("-")
                    and len(part) > 3
                    and not part.startswith("http")
                ):
                    file_paths.append(part)

        return file_paths

    def _get_operation_type(self, tool_name: str) -> str:
        """Map tool name to operation type"""
        mapping = {
            "Read": "read",
            "Write": "write",
            "Edit": "edit",
            "MultiEdit": "edit",
            "Bash": "execute",
            "Glob": "search",
            "Grep": "search",
        }
        return mapping.get(tool_name, "unknown")

    def _get_file_type_distribution(self, file_paths: List[str]) -> Dict[str, int]:
        """Get distribution of file types"""
        extensions = {}
        for file_path in file_paths:
            ext = Path(file_path).suffix.lower()
            if not ext:
                ext = "no_extension"
            extensions[ext] = extensions.get(ext, 0) + 1
        return extensions

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "total_file_operations": {"type": "integer"},
                "unique_files_accessed": {"type": "integer"},
                "file_statistics": {"type": "object"},
                "file_type_distribution": {"type": "object"},
            },
        }


class URLAccessExtractor(AnalyticsComponent):
    """Extracts URL access analytics"""

    def __init__(self):
        super().__init__("URLAccessExtractor")
        self.web_tools = {
            "WebSearch",
            "WebFetch",
            "brave_web_search",
            "brave_news_search",
            "firecrawl_scrape",
            "firecrawl_search",
            "mcp__web_search__brave_web_search",
        }

    def analyze(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract URL access analytics"""
        records = session_data.get("records", [])
        url_accesses = []

        for record in records:
            if record.get("type") == "assistant":
                content = record.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name")
                            tool_input = item.get("input", {})

                            if tool_name in self.web_tools:
                                urls = self._extract_urls(tool_name, tool_input)

                                for url in urls:
                                    url_accesses.append(
                                        {
                                            "url": url,
                                            "tool_name": tool_name,
                                            "timestamp": record.get("timestamp"),
                                            "purpose": self._classify_purpose(
                                                tool_name, tool_input
                                            ),
                                        }
                                    )

        # Aggregate URL statistics
        unique_urls = set(access["url"] for access in url_accesses)
        tool_usage = {}
        purpose_distribution = {}

        for access in url_accesses:
            tool_name = access["tool_name"]
            purpose = access["purpose"]

            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
            purpose_distribution[purpose] = purpose_distribution.get(purpose, 0) + 1

        return {
            "total_url_accesses": len(url_accesses),
            "unique_urls": len(unique_urls),
            "tool_usage_distribution": tool_usage,
            "purpose_distribution": purpose_distribution,
            "access_details": url_accesses,
        }

    def _extract_urls(self, tool_name: str, tool_input: Dict) -> List[str]:
        """Extract URLs from tool input"""
        urls = []

        # Common URL parameter names
        url_params = ["url", "urls", "query", "search_term"]

        for param in url_params:
            if param in tool_input:
                value = tool_input[param]
                if isinstance(value, str) and ("http" in value or "www." in value):
                    urls.append(value)
                elif isinstance(value, list):
                    urls.extend(
                        [v for v in value if isinstance(v, str) and "http" in v]
                    )

        return urls

    def _classify_purpose(self, tool_name: str, tool_input: Dict) -> str:
        """Classify the purpose of the URL access"""
        if "search" in tool_name.lower():
            return "search"
        elif "scrape" in tool_name.lower() or "fetch" in tool_name.lower():
            return "content_extraction"
        elif "news" in tool_name.lower():
            return "news_lookup"
        else:
            return "general_web_access"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "total_url_accesses": {"type": "integer"},
                "unique_urls": {"type": "integer"},
                "tool_usage_distribution": {"type": "object"},
                "purpose_distribution": {"type": "object"},
                "access_details": {"type": "array"},
            },
        }


class ConversationFlowExtractor(AnalyticsComponent):
    """Extracts conversation flow and patterns"""

    def __init__(self):
        super().__init__("ConversationFlowExtractor")

    def analyze(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract conversation flow analytics"""
        records = session_data.get("records", [])

        # Filter to user and assistant messages only
        messages = []
        for record in records:
            if record.get("type") in ["user", "assistant"]:
                messages.append(
                    {
                        "type": record["type"],
                        "timestamp": record.get("timestamp"),
                        "content": self._extract_content(record),
                        "uuid": record.get("uuid"),
                        "parent_uuid": record.get("parentUuid"),
                    }
                )

        # Build conversation flow
        flow_analysis = {
            "total_turns": len(messages),
            "user_messages": len([m for m in messages if m["type"] == "user"]),
            "assistant_messages": len(
                [m for m in messages if m["type"] == "assistant"]
            ),
            "conversation_threads": self._identify_threads(messages),
            "message_lengths": self._analyze_message_lengths(messages),
            "response_patterns": self._analyze_response_patterns(messages),
            "topic_shifts": self._identify_topic_shifts(messages),
        }

        return flow_analysis

    def _extract_content(self, record: Dict) -> str:
        """Extract content from message record"""
        message = record.get("message", {})
        content = message.get("content", "")

        if isinstance(content, list):
            # Handle structured content
            text_parts = []
            for item in content:
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif item.get("type") == "tool_use":
                    text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
                elif item.get("type") == "tool_result":
                    text_parts.append("[Tool Result]")
            content = " ".join(text_parts)

        return str(content)

    def _identify_threads(self, messages: List[Dict]) -> List[Dict]:
        """Identify conversation threads based on parent relationships"""
        threads = []
        message_map = {msg["uuid"]: msg for msg in messages if msg.get("uuid")}

        # Find root messages (no parent)
        roots = [msg for msg in messages if not msg.get("parent_uuid")]

        for root in roots:
            thread = {
                "root_message": root["uuid"],
                "length": 1,
                "participants": {root["type"]},
                "duration": None,
            }

            # Trace children
            current = root
            while current:
                children = [
                    msg
                    for msg in messages
                    if msg.get("parent_uuid") == current.get("uuid")
                ]
                if children:
                    child = children[0]  # Take first child
                    thread["length"] += 1
                    thread["participants"].add(child["type"])
                    current = child
                else:
                    break

            thread["participants"] = list(thread["participants"])
            threads.append(thread)

        return threads

    def _analyze_message_lengths(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze message length patterns"""
        lengths_by_type = {"user": [], "assistant": []}

        for msg in messages:
            content_length = len(msg.get("content", ""))
            if msg["type"] in lengths_by_type:
                lengths_by_type[msg["type"]].append(content_length)

        analysis = {}
        for msg_type, lengths in lengths_by_type.items():
            if lengths:
                analysis[f"{msg_type}_avg_length"] = sum(lengths) / len(lengths)
                analysis[f"{msg_type}_max_length"] = max(lengths)
                analysis[f"{msg_type}_min_length"] = min(lengths)
            else:
                analysis[f"{msg_type}_avg_length"] = 0
                analysis[f"{msg_type}_max_length"] = 0
                analysis[f"{msg_type}_min_length"] = 0

        return analysis

    def _analyze_response_patterns(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze response patterns between user and assistant"""
        patterns = {
            "user_initiated_chains": 0,
            "assistant_followup_rate": 0,
            "average_chain_length": 0,
        }

        # Simple pattern analysis
        user_messages = [m for m in messages if m["type"] == "user"]
        assistant_messages = [m for m in messages if m["type"] == "assistant"]

        patterns["user_initiated_chains"] = len(user_messages)

        if user_messages:
            patterns["assistant_followup_rate"] = len(assistant_messages) / len(
                user_messages
            )

        return patterns

    def _identify_topic_shifts(self, messages: List[Dict]) -> List[Dict]:
        """Identify potential topic shifts in conversation"""
        # Simplified topic shift detection based on content analysis
        shifts = []

        if len(messages) < 2:
            return shifts

        prev_keywords = set()

        for i, msg in enumerate(messages[1:], 1):
            current_content = msg.get("content", "").lower()
            current_keywords = set(
                word
                for word in current_content.split()
                if len(word) > 4 and word.isalpha()
            )

            if prev_keywords and current_keywords:
                # Calculate keyword overlap
                overlap = len(prev_keywords & current_keywords) / len(
                    prev_keywords | current_keywords
                )

                if overlap < 0.3:  # Low overlap indicates topic shift
                    shifts.append(
                        {
                            "position": i,
                            "message_uuid": msg.get("uuid"),
                            "overlap_score": overlap,
                            "shift_strength": "high" if overlap < 0.1 else "medium",
                        }
                    )

            prev_keywords = current_keywords

        return shifts

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "total_turns": {"type": "integer"},
                "user_messages": {"type": "integer"},
                "assistant_messages": {"type": "integer"},
                "conversation_threads": {"type": "array"},
                "message_lengths": {"type": "object"},
                "response_patterns": {"type": "object"},
                "topic_shifts": {"type": "array"},
            },
        }


# Component registry for easy extension
AVAILABLE_COMPONENTS = {
    "session_metrics": SessionMetricsExtractor,
    "tool_usage": ToolUsageExtractor,
    "file_activity": FileActivityExtractor,
    "url_access": URLAccessExtractor,
    "conversation_flow": ConversationFlowExtractor,
}


class ComponentRegistry:
    """Registry for managing analytics components"""

    def __init__(self):
        self.components = {}
        self.logger = logging.getLogger(__name__)

    def register_component(self, name: str, component_class: type):
        """Register a new analytics component"""
        if not issubclass(component_class, AnalyticsComponent):
            raise ValueError("Component must extend AnalyticsComponent")

        self.components[name] = component_class
        self.logger.info(f"Registered component: {name}")

    def get_component(self, name: str) -> AnalyticsComponent:
        """Get an instance of a registered component"""
        if name not in self.components:
            raise KeyError(f"Component '{name}' not registered")

        return self.components[name]()

    def list_components(self) -> List[str]:
        """List all registered component names"""
        return list(self.components.keys())

    def run_all_components(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run all registered components on session data"""
        results = {}

        for name, component_class in self.components.items():
            try:
                component = component_class()
                results[name] = component.analyze(session_data)
                self.logger.info(f"Successfully ran component: {name}")
            except Exception as e:
                self.logger.error(f"Error running component {name}: {e}")
                results[name] = {"error": str(e)}

        return results


# Initialize default registry
default_registry = ComponentRegistry()
for name, component_class in AVAILABLE_COMPONENTS.items():
    default_registry.register_component(name, component_class)
