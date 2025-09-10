#!/usr/bin/env python3
"""
SessionAnalyticsEngine - Comprehensive session log analytics system
Extends existing chat parsing infrastructure to analyze Claude session logs from .jsonl files.

Provides comprehensive analytics including:
- Start/end times and duration
- Message counts and conversation patterns
- File operations and URL access tracking
- Tool usage analytics
- Conversation flow analysis
- Cross-session pattern recognition
"""

import hashlib
import json
import logging
import os
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import existing infrastructure components
try:
    import sys

    sys.path.append("/home/opsvi/master_root/libs")
    from chat_report_generator import SessionAnalyzer
    from chat_taxonomy_parser import (
        ChatLogParser,
        FileOperation,
        Node,
        Session,
        ToolCall,
        ToolResult,
    )
except ImportError:
    logging.warning(
        "Could not import existing chat infrastructure - using minimal implementations"
    )
    # Minimal fallback implementations will be provided


@dataclass
class SessionMetrics:
    """Core session metrics"""

    session_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    total_messages: int
    user_messages: int
    assistant_messages: int
    system_messages: int
    total_tool_calls: int
    unique_tools_used: int
    total_file_operations: int
    unique_files_touched: int
    total_urls_accessed: int
    conversation_turns: int
    working_directory: str
    git_branch: str


@dataclass
class ConversationPattern:
    """Conversation pattern analysis"""

    session_id: str
    pattern_type: str  # 'question_answer', 'iterative_refinement', 'task_completion', 'exploration'
    frequency: int
    average_response_time: float
    context_switches: int
    topic_coherence_score: float


@dataclass
class ToolUsageAnalytics:
    """Tool usage analytics"""

    session_id: str
    tool_name: str
    usage_count: int
    success_rate: float
    average_execution_time: float
    error_patterns: List[str]
    parameter_patterns: Dict[str, Any]


@dataclass
class FileOperationAnalytics:
    """File operation analytics"""

    session_id: str
    file_path: str
    operations: List[str]  # 'read', 'write', 'edit'
    total_operations: int
    lines_modified: int
    content_hash_changes: List[str]
    modification_frequency: float


class SessionLogParser:
    """Parses Claude session .jsonl files from project directories"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def find_session_files(
        self, claude_project_root: Optional[str] = None
    ) -> List[Path]:
        """Find all .jsonl session files in Claude project directories"""
        if claude_project_root is None:
            claude_project_root = os.environ.get(
                "CLAUDE_PROJECT_ROOT", "/home/opsvi/.claude/projects"
            )

        project_root = Path(claude_project_root)
        if not project_root.exists():
            self.logger.warning(f"Claude project root not found: {project_root}")
            return []

        session_files = list(project_root.rglob("*.jsonl"))
        self.logger.info(f"Found {len(session_files)} session files in {project_root}")
        return session_files

    def parse_session_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single .jsonl session file"""
        session_data = {
            "file_path": str(file_path),
            "session_id": file_path.stem,  # Use filename as session ID
            "project_path": str(file_path.parent.name),
            "records": [],
            "metadata": {},
        }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                        session_data["records"].append(record)

                        # Extract session metadata from first record
                        if line_num == 1 or "sessionId" in record:
                            session_data["metadata"].update(
                                {
                                    "session_id": record.get(
                                        "sessionId", session_data["session_id"]
                                    ),
                                    "cwd": record.get("cwd", ""),
                                    "git_branch": record.get("git_branch", ""),
                                    "version": record.get("version", ""),
                                    "user_type": record.get("userType", ""),
                                }
                            )

                    except json.JSONDecodeError as e:
                        self.logger.error(
                            f"JSON decode error in {file_path}:{line_num}: {e}"
                        )
                        continue

        except Exception as e:
            self.logger.error(f"Error reading session file {file_path}: {e}")
            return None

        return session_data

    def extract_timestamps(
        self, session_data: Dict[str, Any]
    ) -> Tuple[datetime, datetime]:
        """Extract start and end timestamps from session data"""
        timestamps = []

        for record in session_data["records"]:
            timestamp_str = record.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                    timestamps.append(timestamp)
                except (ValueError, TypeError):
                    continue

        if not timestamps:
            # Fallback to file modification time
            file_path = Path(session_data["file_path"])
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_time, file_time

        return min(timestamps), max(timestamps)


class ConversationAnalyzer:
    """Analyzes conversation patterns and flow"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_conversation_patterns(
        self, session_data: Dict[str, Any]
    ) -> List[ConversationPattern]:
        """Analyze conversation patterns in the session"""
        patterns = []
        records = session_data["records"]
        session_id = session_data["metadata"].get("session_id", "unknown")

        # Track conversation turns
        conversation_turns = 0
        context_switches = 0
        response_times = []

        user_messages = []
        assistant_messages = []

        for record in records:
            record_type = record.get("type")
            if record_type == "user":
                user_messages.append(record)
                conversation_turns += 1
            elif record_type == "assistant":
                assistant_messages.append(record)

        # Calculate response times (simplified)
        for i in range(min(len(user_messages), len(assistant_messages)) - 1):
            try:
                user_time = datetime.fromisoformat(
                    user_messages[i]["timestamp"].replace("Z", "+00:00")
                )
                assistant_time = datetime.fromisoformat(
                    assistant_messages[i]["timestamp"].replace("Z", "+00:00")
                )
                response_time = (assistant_time - user_time).total_seconds()
                response_times.append(response_time)
            except (KeyError, ValueError):
                continue

        # Determine pattern type based on message characteristics
        pattern_type = self._classify_conversation_pattern(
            user_messages, assistant_messages
        )

        # Calculate metrics
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )
        topic_coherence = self._calculate_topic_coherence(
            user_messages + assistant_messages
        )

        pattern = ConversationPattern(
            session_id=session_id,
            pattern_type=pattern_type,
            frequency=conversation_turns,
            average_response_time=avg_response_time,
            context_switches=context_switches,
            topic_coherence_score=topic_coherence,
        )

        patterns.append(pattern)
        return patterns

    def _classify_conversation_pattern(
        self, user_messages: List[Dict], assistant_messages: List[Dict]
    ) -> str:
        """Classify the conversation pattern based on message content"""
        if not user_messages:
            return "unknown"

        # Simple heuristics for pattern classification
        total_messages = len(user_messages) + len(assistant_messages)

        if total_messages < 4:
            return "question_answer"
        elif total_messages > 20:
            return "exploration"
        else:
            # Check for iterative refinement patterns
            question_words = ["how", "what", "why", "can you", "please"]
            refinement_words = ["fix", "change", "update", "modify", "improve"]

            user_content = " ".join(
                [msg.get("message", {}).get("content", "") for msg in user_messages]
            ).lower()

            if any(word in user_content for word in refinement_words):
                return "iterative_refinement"
            elif any(word in user_content for word in question_words):
                return "task_completion"
            else:
                return "exploration"

    def _calculate_topic_coherence(self, messages: List[Dict]) -> float:
        """Calculate topic coherence score (simplified implementation)"""
        if not messages:
            return 0.0

        # Extract keywords from messages
        keywords = set()
        for msg in messages:
            content = str(msg.get("message", {}).get("content", ""))
            # Simple keyword extraction (in production, use NLP libraries)
            words = re.findall(r"\b\w{4,}\b", content.lower())
            keywords.update(words)

        # Simple coherence metric based on keyword repetition
        if not keywords:
            return 0.0

        word_counts = Counter()
        for msg in messages:
            content = str(msg.get("message", {}).get("content", ""))
            words = re.findall(r"\b\w{4,}\b", content.lower())
            word_counts.update(words)

        # Calculate coherence as ratio of repeated keywords
        repeated_keywords = sum(1 for count in word_counts.values() if count > 1)
        coherence_score = repeated_keywords / len(keywords) if keywords else 0.0

        return min(coherence_score, 1.0)


class ToolUsageAnalyzer:
    """Analyzes tool usage patterns and performance"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_tool_usage(
        self, session_data: Dict[str, Any]
    ) -> List[ToolUsageAnalytics]:
        """Analyze tool usage patterns in the session"""
        tool_analytics = []
        session_id = session_data["metadata"].get("session_id", "unknown")

        # Track tool calls and results
        tool_calls = {}  # tool_use_id -> tool_call_data
        tool_results = {}  # tool_use_id -> result_data

        for record in session_data["records"]:
            if record.get("type") == "assistant":
                content = record.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_use":
                            tool_use_id = item.get("id")
                            tool_calls[tool_use_id] = {
                                "name": item.get("name"),
                                "input": item.get("input", {}),
                                "timestamp": record.get("timestamp"),
                            }

            elif record.get("type") == "user":
                content = record.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_result":
                            tool_use_id = item.get("tool_use_id")
                            tool_results[tool_use_id] = {
                                "is_error": item.get("is_error", False),
                                "content": item.get("content", ""),
                                "timestamp": record.get("timestamp"),
                            }

        # Aggregate tool usage data
        tool_usage_data = defaultdict(list)
        for tool_use_id, tool_call in tool_calls.items():
            tool_name = tool_call["name"]
            result = tool_results.get(tool_use_id, {})

            tool_usage_data[tool_name].append(
                {
                    "tool_use_id": tool_use_id,
                    "success": not result.get("is_error", False),
                    "input": tool_call["input"],
                    "timestamp": tool_call["timestamp"],
                }
            )

        # Create analytics for each tool
        for tool_name, usages in tool_usage_data.items():
            success_count = sum(1 for usage in usages if usage["success"])
            success_rate = success_count / len(usages) if usages else 0

            error_patterns = []
            parameter_patterns = defaultdict(int)

            for usage in usages:
                if not usage["success"]:
                    error_patterns.append("execution_error")  # Simplified

                # Analyze parameter patterns
                for key, value in usage["input"].items():
                    parameter_patterns[key] += 1

            analytics = ToolUsageAnalytics(
                session_id=session_id,
                tool_name=tool_name,
                usage_count=len(usages),
                success_rate=success_rate,
                average_execution_time=0.0,  # Would need more detailed timing data
                error_patterns=error_patterns,
                parameter_patterns=dict(parameter_patterns),
            )

            tool_analytics.append(analytics)

        return tool_analytics


class FileOperationAnalyzer:
    """Analyzes file operations and modifications"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_file_operations(
        self, session_data: Dict[str, Any]
    ) -> List[FileOperationAnalytics]:
        """Analyze file operations in the session"""
        file_analytics = []
        session_id = session_data["metadata"].get("session_id", "unknown")

        # Track file operations
        file_operations = defaultdict(list)

        for record in session_data["records"]:
            if record.get("type") == "assistant":
                content = record.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name", "")
                            tool_input = item.get("input", {})

                            # File operation tools
                            if tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
                                file_path = tool_input.get("file_path", "")
                                if file_path:
                                    operation_type = self._get_operation_type(tool_name)
                                    file_operations[file_path].append(
                                        {
                                            "operation": operation_type,
                                            "timestamp": record.get("timestamp"),
                                            "tool_input": tool_input,
                                        }
                                    )

        # Create analytics for each file
        for file_path, operations in file_operations.items():
            operation_types = [op["operation"] for op in operations]
            lines_modified = self._calculate_lines_modified(operations)

            analytics = FileOperationAnalytics(
                session_id=session_id,
                file_path=file_path,
                operations=operation_types,
                total_operations=len(operations),
                lines_modified=lines_modified,
                content_hash_changes=[],  # Would need content analysis
                modification_frequency=len(operations)
                / max(1, len(session_data["records"])),
            )

            file_analytics.append(analytics)

        return file_analytics

    def _get_operation_type(self, tool_name: str) -> str:
        """Map tool name to operation type"""
        mapping = {
            "Read": "read",
            "Write": "write",
            "Edit": "edit",
            "MultiEdit": "edit",
        }
        return mapping.get(tool_name, "unknown")

    def _calculate_lines_modified(self, operations: List[Dict]) -> int:
        """Calculate approximate lines modified"""
        lines_modified = 0

        for op in operations:
            tool_input = op.get("tool_input", {})

            # For Write operations, count content lines
            if op["operation"] == "write":
                content = tool_input.get("content", "")
                lines_modified += len(content.splitlines()) if content else 1

            # For Edit operations, use old_string/new_string
            elif op["operation"] == "edit":
                old_string = tool_input.get("old_string", "")
                new_string = tool_input.get("new_string", "")
                lines_modified += max(
                    len(old_string.splitlines()) if old_string else 0,
                    len(new_string.splitlines()) if new_string else 0,
                )

        return lines_modified


class SessionAnalyticsEngine:
    """Main analytics engine that coordinates all analysis components"""

    def __init__(self, claude_project_root: Optional[str] = None):
        self.claude_project_root = claude_project_root or os.environ.get(
            "CLAUDE_PROJECT_ROOT", "/home/opsvi/.claude/projects"
        )
        self.logger = logging.getLogger(__name__)

        # Initialize component analyzers
        self.session_parser = SessionLogParser()
        self.conversation_analyzer = ConversationAnalyzer()
        self.tool_analyzer = ToolUsageAnalyzer()
        self.file_analyzer = FileOperationAnalyzer()

        # Results cache
        self.session_metrics_cache = {}
        self.analytics_cache = {}

    def analyze_all_sessions(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Analyze all session files and return comprehensive analytics"""
        self.logger.info("Starting comprehensive session analysis")

        # Find all session files
        session_files = self.session_parser.find_session_files(self.claude_project_root)

        if not session_files:
            self.logger.warning("No session files found")
            return {}

        # Analyze each session
        all_metrics = []
        all_patterns = []
        all_tool_analytics = []
        all_file_analytics = []

        for session_file in session_files:
            try:
                metrics, patterns, tools, files = self.analyze_single_session(
                    session_file
                )

                if metrics:
                    all_metrics.append(metrics)
                    all_patterns.extend(patterns)
                    all_tool_analytics.extend(tools)
                    all_file_analytics.extend(files)

            except Exception as e:
                self.logger.error(f"Error analyzing session {session_file}: {e}")
                continue

        # Aggregate results
        results = {
            "summary": self._generate_summary(all_metrics),
            "session_metrics": all_metrics,
            "conversation_patterns": all_patterns,
            "tool_usage_analytics": all_tool_analytics,
            "file_operation_analytics": all_file_analytics,
            "cross_session_insights": self._generate_cross_session_insights(
                all_metrics, all_patterns, all_tool_analytics, all_file_analytics
            ),
        }

        self.logger.info(f"Analysis complete. Processed {len(all_metrics)} sessions")
        return results

    def analyze_single_session(
        self, session_file: Path
    ) -> Tuple[
        SessionMetrics,
        List[ConversationPattern],
        List[ToolUsageAnalytics],
        List[FileOperationAnalytics],
    ]:
        """Analyze a single session file"""
        # Parse session data
        session_data = self.session_parser.parse_session_file(session_file)
        if not session_data:
            return None, [], [], []

        # Extract basic metrics
        start_time, end_time = self.session_parser.extract_timestamps(session_data)
        duration = (end_time - start_time).total_seconds() / 60.0

        # Count messages by type
        message_counts = self._count_messages(session_data["records"])
        tool_counts = self._count_tools(session_data["records"])
        file_counts = self._count_files(session_data["records"])
        url_counts = self._count_urls(session_data["records"])

        # Create session metrics
        metrics = SessionMetrics(
            session_id=session_data["metadata"].get("session_id", session_file.stem),
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            total_messages=message_counts["total"],
            user_messages=message_counts["user"],
            assistant_messages=message_counts["assistant"],
            system_messages=message_counts["system"],
            total_tool_calls=tool_counts["total"],
            unique_tools_used=tool_counts["unique"],
            total_file_operations=file_counts["operations"],
            unique_files_touched=file_counts["unique_files"],
            total_urls_accessed=url_counts,
            conversation_turns=message_counts["user"],  # Approximation
            working_directory=session_data["metadata"].get("cwd", ""),
            git_branch=session_data["metadata"].get("git_branch", ""),
        )

        # Run detailed analysis
        patterns = self.conversation_analyzer.analyze_conversation_patterns(
            session_data
        )
        tool_analytics = self.tool_analyzer.analyze_tool_usage(session_data)
        file_analytics = self.file_analyzer.analyze_file_operations(session_data)

        return metrics, patterns, tool_analytics, file_analytics

    def _count_messages(self, records: List[Dict]) -> Dict[str, int]:
        """Count messages by type"""
        counts = {"total": 0, "user": 0, "assistant": 0, "system": 0}

        for record in records:
            record_type = record.get("type", "unknown")
            if record_type in ["user", "assistant", "system"]:
                counts[record_type] += 1
                counts["total"] += 1

        return counts

    def _count_tools(self, records: List[Dict]) -> Dict[str, int]:
        """Count tool usage"""
        tool_names = set()
        total_calls = 0

        for record in records:
            if record.get("type") == "assistant":
                content = record.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_use":
                            tool_names.add(item.get("name"))
                            total_calls += 1

        return {"total": total_calls, "unique": len(tool_names)}

    def _count_files(self, records: List[Dict]) -> Dict[str, int]:
        """Count file operations"""
        file_paths = set()
        total_operations = 0

        for record in records:
            if record.get("type") == "assistant":
                content = record.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name", "")
                            if tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
                                file_path = item.get("input", {}).get("file_path")
                                if file_path:
                                    file_paths.add(file_path)
                                    total_operations += 1

        return {"operations": total_operations, "unique_files": len(file_paths)}

    def _count_urls(self, records: List[Dict]) -> int:
        """Count URL accesses"""
        url_count = 0

        for record in records:
            if record.get("type") == "assistant":
                content = record.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name", "")
                            if "web" in tool_name.lower() or "url" in tool_name.lower():
                                url_count += 1

        return url_count

    def _generate_summary(self, metrics_list: List[SessionMetrics]) -> Dict[str, Any]:
        """Generate high-level summary statistics"""
        if not metrics_list:
            return {}

        total_sessions = len(metrics_list)
        total_duration = sum(m.duration_minutes for m in metrics_list)
        total_messages = sum(m.total_messages for m in metrics_list)
        total_tools = sum(m.total_tool_calls for m in metrics_list)
        total_files = sum(m.total_file_operations for m in metrics_list)

        return {
            "total_sessions": total_sessions,
            "total_duration_hours": total_duration / 60.0,
            "average_session_duration_minutes": total_duration / total_sessions,
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / total_sessions,
            "total_tool_calls": total_tools,
            "average_tools_per_session": total_tools / total_sessions,
            "total_file_operations": total_files,
            "unique_working_directories": len(
                set(m.working_directory for m in metrics_list)
            ),
            "unique_git_branches": len(
                set(m.git_branch for m in metrics_list if m.git_branch)
            ),
        }

    def _generate_cross_session_insights(
        self,
        metrics: List[SessionMetrics],
        patterns: List[ConversationPattern],
        tools: List[ToolUsageAnalytics],
        files: List[FileOperationAnalytics],
    ) -> Dict[str, Any]:
        """Generate insights across all sessions"""
        insights = {}

        if metrics:
            # Time patterns
            session_hours = [m.start_time.hour for m in metrics]
            insights["peak_usage_hours"] = Counter(session_hours).most_common(3)

            # Duration patterns
            durations = [m.duration_minutes for m in metrics]
            insights["session_duration_patterns"] = {
                "short_sessions_under_5min": len([d for d in durations if d < 5]),
                "medium_sessions_5_30min": len([d for d in durations if 5 <= d < 30]),
                "long_sessions_over_30min": len([d for d in durations if d >= 30]),
            }

        if tools:
            # Tool popularity
            tool_usage = Counter(t.tool_name for t in tools)
            insights["most_popular_tools"] = tool_usage.most_common(10)

            # Success rates
            tool_success_rates = {}
            for tool in tools:
                if tool.tool_name not in tool_success_rates:
                    tool_success_rates[tool.tool_name] = []
                tool_success_rates[tool.tool_name].append(tool.success_rate)

            insights["tool_reliability"] = {
                tool: sum(rates) / len(rates)
                for tool, rates in tool_success_rates.items()
            }

        if files:
            # File patterns
            file_types = Counter()
            for file_analytics in files:
                file_ext = Path(file_analytics.file_path).suffix
                file_types[file_ext] += 1

            insights["file_type_distribution"] = file_types.most_common(10)

            # Modification patterns
            heavy_edit_files = [f for f in files if f.total_operations > 5]
            insights["heavily_modified_files"] = len(heavy_edit_files)

        return insights

    def export_analytics(
        self, results: Dict[str, Any], output_path: str, format: str = "json"
    ) -> bool:
        """Export analytics results to file"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if format.lower() == "json":
                # Convert dataclasses to dictionaries for JSON serialization
                serializable_results = self._make_serializable(results)
                with open(output_file, "w") as f:
                    json.dump(serializable_results, f, indent=2, default=str)

            else:
                raise ValueError(f"Unsupported export format: {format}")

            self.logger.info(f"Analytics exported to {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export analytics: {e}")
            return False

    def _make_serializable(self, obj: Any) -> Any:
        """Convert dataclasses and other objects to JSON-serializable format"""
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        else:
            return obj


# Usage example and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize analytics engine
    engine = SessionAnalyticsEngine()

    # Run comprehensive analysis
    results = engine.analyze_all_sessions()

    # Print summary
    if results:
        print("Session Analytics Summary:")
        print("=" * 40)

        summary = results.get("summary", {})
        for key, value in summary.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        print(f"\nTotal Sessions Analyzed: {len(results.get('session_metrics', []))}")
        print(
            f"Total Conversation Patterns: {len(results.get('conversation_patterns', []))}"
        )
        print(f"Total Tool Analytics: {len(results.get('tool_usage_analytics', []))}")
        print(
            f"Total File Analytics: {len(results.get('file_operation_analytics', []))}"
        )

        # Export results
        engine.export_analytics(
            results,
            "/home/opsvi/master_root/apps/agent-orchestrator/output/session_analytics_results.json",
        )

    else:
        print("No session data found or analysis failed")
