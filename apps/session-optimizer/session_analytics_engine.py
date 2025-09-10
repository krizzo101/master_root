#!/usr/bin/env python3
"""
SessionAnalyticsEngine Implementation
Built on Phase 1 analysis results for Claude session optimization.

This modular system provides:
- LogParser: Parse Claude .jsonl files
- ConversationAnalyzer: Extract dialog patterns
- ToolAnalyzer: Track tool usage patterns
- FileAnalyzer: Monitor file operation patterns
- SessionMetrics: Calculate comprehensive statistics

Based on existing chat_taxonomy_parser.py infrastructure.
"""

import hashlib
import json
import re
import statistics
import uuid as uuid_lib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class SessionContext:
    """Session context information"""

    session_id: str
    project_name: str = ""
    working_directory: str = ""
    git_branch: str = ""
    created_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class MessageNode:
    """Represents a single message/interaction node"""

    uuid: str
    session_id: str
    parent_uuid: Optional[str]
    node_type: str  # 'user', 'assistant', 'system'
    timestamp: datetime
    content_hash: str
    token_count: int = 0
    raw_content: Any = None
    tool_calls: List = field(default_factory=list)
    tool_results: List = field(default_factory=list)


@dataclass
class ConversationFlow:
    """Represents dialog flow patterns"""

    session_id: str
    user_messages: int = 0
    assistant_messages: int = 0
    system_messages: int = 0
    avg_response_time: float = 0.0
    conversation_length: int = 0
    topic_shifts: int = 0
    patterns: List[str] = field(default_factory=list)


@dataclass
class ToolUsageMetrics:
    """Tool usage analysis"""

    session_id: str
    tool_counts: Dict[str, int] = field(default_factory=dict)
    tool_categories: Dict[str, int] = field(default_factory=dict)
    tool_success_rate: Dict[str, float] = field(default_factory=dict)
    tool_sequences: List[List[str]] = field(default_factory=list)
    mcp_tools_used: Set[str] = field(default_factory=set)


@dataclass
class FileOperationMetrics:
    """File operation analysis"""

    session_id: str
    files_read: Set[str] = field(default_factory=set)
    files_written: Set[str] = field(default_factory=set)
    files_edited: Set[str] = field(default_factory=set)
    operation_counts: Dict[str, int] = field(default_factory=dict)
    file_hotspots: List[Tuple[str, int]] = field(default_factory=list)
    edit_patterns: List[str] = field(default_factory=list)


@dataclass
class SessionAnalysisReport:
    """Comprehensive session analysis results"""

    session_context: SessionContext
    conversation_flow: ConversationFlow
    tool_usage: ToolUsageMetrics
    file_operations: FileOperationMetrics
    optimization_score: float = 0.0
    complexity_rating: str = "Unknown"
    recommended_chunks: int = 1
    cost_estimate: float = 0.0
    patterns_detected: List[str] = field(default_factory=list)


class LogParser:
    """Parse Claude .jsonl log files with optimized processing"""

    def __init__(self):
        self.tool_patterns = {
            "file_ops": {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"},
            "shell_ops": {"Bash", "mcp__shell_exec__shell_exec", "Grep", "Glob"},
            "web_ops": {
                "WebSearch",
                "WebFetch",
                "mcp__web_search__brave_web_search",
                "mcp__web_search__brave_news_search",
                "mcp__firecrawl__firecrawl_scrape",
            },
            "knowledge": {
                "mcp__knowledge__knowledge_store",
                "mcp__knowledge__knowledge_query",
                "mcp__knowledge__knowledge_smart_query",
            },
            "planning": {"TodoWrite", "ExitPlanMode"},
            "agent": {"Task"},
            "mcp_tools": re.compile(r"mcp__(\w+)__(\w+)"),
        }

    def parse_session_file(self, jsonl_path: Path) -> List[MessageNode]:
        """Parse a single .jsonl session file"""
        nodes = []
        session_id = None

        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)

                        # Extract session ID from first record
                        if session_id is None:
                            session_id = record.get("sessionId", str(jsonl_path.stem))

                        node = self._parse_record(record, session_id)
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

    def _parse_record(self, record: Dict, session_id: str) -> Optional[MessageNode]:
        """Parse individual JSONL record into MessageNode"""
        record_type = record.get("type")
        if not record_type:
            return None

        node = MessageNode(
            uuid=record.get("uuid", str(uuid_lib.uuid4())),
            session_id=session_id,
            parent_uuid=record.get("parentUuid"),
            node_type=record_type,
            timestamp=self._parse_timestamp(record.get("timestamp")),
            content_hash=self._hash_content(str(record.get("message", {}))),
            raw_content=record.get("message", {}),
        )

        # Extract tool calls and results from assistant messages
        if record_type == "assistant":
            self._extract_tool_usage(record, node)

        # Estimate token count (rough approximation)
        node.token_count = self._estimate_tokens(record)

        return node

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return datetime.now()

        try:
            # Handle ISO format with/without timezone
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except:
            return datetime.now()

    def _hash_content(self, content: str) -> str:
        """Generate SHA256 hash for content deduplication"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _extract_tool_usage(self, record: Dict, node: MessageNode):
        """Extract tool calls and results from assistant message"""
        content = record.get("message", {}).get("content", [])
        if not isinstance(content, list):
            return

        for item in content:
            if item.get("type") == "tool_use":
                node.tool_calls.append(
                    {
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "input": item.get("input", {}),
                    }
                )
            elif item.get("type") == "tool_result":
                node.tool_results.append(
                    {
                        "tool_use_id": item.get("tool_use_id"),
                        "is_error": item.get("is_error", False),
                        "content": str(item.get("content", "")),
                    }
                )

    def _estimate_tokens(self, record: Dict) -> int:
        """Rough token count estimation (1 token ≈ 4 characters)"""
        content_str = json.dumps(record, ensure_ascii=False)
        return max(1, len(content_str) // 4)


class ConversationAnalyzer:
    """Analyze dialog patterns and conversation flows"""

    def analyze_conversation(self, nodes: List[MessageNode]) -> ConversationFlow:
        """Analyze conversation patterns from message nodes"""
        if not nodes:
            return ConversationFlow(session_id="unknown")

        session_id = nodes[0].session_id
        flow = ConversationFlow(session_id=session_id)

        # Count message types
        type_counts = Counter(node.node_type for node in nodes)
        flow.user_messages = type_counts.get("user", 0)
        flow.assistant_messages = type_counts.get("assistant", 0)
        flow.system_messages = type_counts.get("system", 0)
        flow.conversation_length = len(nodes)

        # Calculate response times
        response_times = self._calculate_response_times(nodes)
        flow.avg_response_time = (
            statistics.mean(response_times) if response_times else 0.0
        )

        # Detect conversation patterns
        flow.patterns = self._detect_conversation_patterns(nodes)
        flow.topic_shifts = self._count_topic_shifts(nodes)

        return flow

    def _calculate_response_times(self, nodes: List[MessageNode]) -> List[float]:
        """Calculate time between user and assistant messages"""
        response_times = []
        user_times = []
        assistant_times = []

        for node in nodes:
            if node.node_type == "user":
                user_times.append(node.timestamp)
            elif node.node_type == "assistant":
                assistant_times.append(node.timestamp)

        # Pair up user and assistant messages
        for i, user_time in enumerate(user_times):
            # Find next assistant response
            next_assistant = None
            for asst_time in assistant_times:
                if asst_time > user_time:
                    next_assistant = asst_time
                    break

            if next_assistant:
                response_time = (next_assistant - user_time).total_seconds()
                response_times.append(response_time)

        return response_times

    def _detect_conversation_patterns(self, nodes: List[MessageNode]) -> List[str]:
        """Detect common conversation patterns"""
        patterns = []

        # Detect session continuation patterns
        for node in nodes[:3]:  # Check first few messages
            if node.node_type == "user" and node.raw_content:
                content = str(node.raw_content.get("content", "")).lower()
                if "continued from" in content or "continuing from" in content:
                    patterns.append("session_continuation")
                if "/status" in content or "/compact" in content:
                    patterns.append("session_management")

        # Detect iterative development patterns
        user_messages = [n for n in nodes if n.node_type == "user"]
        if len(user_messages) > 10:
            patterns.append("extended_development_session")

        # Detect planning patterns (TodoWrite usage)
        tool_names = []
        for node in nodes:
            if node.node_type == "assistant":
                tool_names.extend([tc["name"] for tc in node.tool_calls])

        if "TodoWrite" in tool_names:
            patterns.append("structured_planning")

        return patterns

    def _count_topic_shifts(self, nodes: List[MessageNode]) -> int:
        """Detect major topic shifts in conversation"""
        # Simple heuristic: count user messages that are significantly different
        user_messages = [n for n in nodes if n.node_type == "user"]
        if len(user_messages) < 2:
            return 0

        # Use content hash differences as proxy for topic shifts
        shifts = 0
        prev_hash = user_messages[0].content_hash

        for msg in user_messages[1:]:
            if msg.content_hash != prev_hash:
                shifts += 1
            prev_hash = msg.content_hash

        # More sophisticated topic detection could use NLP here
        return min(shifts, len(user_messages) // 3)  # Cap at reasonable number


class ToolAnalyzer:
    """Analyze tool usage patterns and sequences"""

    def __init__(self):
        self.tool_categories = {
            "file_ops": {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"},
            "shell_ops": {"Bash", "mcp__shell_exec__shell_exec", "Grep", "Glob"},
            "web_ops": {
                "WebSearch",
                "WebFetch",
                "mcp__web_search__brave_web_search",
                "mcp__web_search__brave_news_search",
                "mcp__firecrawl__firecrawl_scrape",
            },
            "knowledge": {
                "mcp__knowledge__knowledge_store",
                "mcp__knowledge__knowledge_query",
            },
            "planning": {"TodoWrite", "ExitPlanMode"},
            "agent": {"Task"},
        }

    def analyze_tool_usage(self, nodes: List[MessageNode]) -> ToolUsageMetrics:
        """Analyze tool usage patterns"""
        if not nodes:
            return ToolUsageMetrics(session_id="unknown")

        session_id = nodes[0].session_id
        metrics = ToolUsageMetrics(session_id=session_id)

        all_tool_calls = []
        success_counts = defaultdict(int)
        error_counts = defaultdict(int)

        for node in nodes:
            if node.node_type == "assistant":
                # Collect tool calls
                for tool_call in node.tool_calls:
                    tool_name = tool_call["name"]
                    all_tool_calls.append(tool_name)
                    metrics.tool_counts[tool_name] = (
                        metrics.tool_counts.get(tool_name, 0) + 1
                    )

                    # Track MCP tools
                    if tool_name.startswith("mcp__"):
                        metrics.mcp_tools_used.add(tool_name)

                # Track tool results for success rates
                for result in node.tool_results:
                    # Find corresponding tool call
                    for tool_call in node.tool_calls:
                        if tool_call["id"] == result["tool_use_id"]:
                            tool_name = tool_call["name"]
                            if result["is_error"]:
                                error_counts[tool_name] += 1
                            else:
                                success_counts[tool_name] += 1
                            break

        # Calculate success rates
        for tool_name in metrics.tool_counts:
            total = success_counts[tool_name] + error_counts[tool_name]
            if total > 0:
                metrics.tool_success_rate[tool_name] = success_counts[tool_name] / total
            else:
                metrics.tool_success_rate[
                    tool_name
                ] = 1.0  # Assume success if no results

        # Categorize tools
        for tool_name, count in metrics.tool_counts.items():
            category = self._categorize_tool(tool_name)
            metrics.tool_categories[category] = (
                metrics.tool_categories.get(category, 0) + count
            )

        # Detect tool sequences (simplified)
        metrics.tool_sequences = self._extract_tool_sequences(all_tool_calls)

        return metrics

    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool by name"""
        for category, tools in self.tool_categories.items():
            if tool_name in tools:
                return category

        if tool_name.startswith("mcp__"):
            return "mcp_tools"

        return "other"

    def _extract_tool_sequences(self, tool_calls: List[str]) -> List[List[str]]:
        """Extract common tool usage sequences"""
        if len(tool_calls) < 2:
            return []

        sequences = []
        current_sequence = [tool_calls[0]]

        for tool in tool_calls[1:]:
            if len(current_sequence) < 5:  # Limit sequence length
                current_sequence.append(tool)
            else:
                sequences.append(current_sequence.copy())
                current_sequence = [tool]

        if len(current_sequence) > 1:
            sequences.append(current_sequence)

        return sequences


class FileAnalyzer:
    """Analyze file operation patterns"""

    def analyze_file_operations(self, nodes: List[MessageNode]) -> FileOperationMetrics:
        """Analyze file operation patterns from tool usage"""
        if not nodes:
            return FileOperationMetrics(session_id="unknown")

        session_id = nodes[0].session_id
        metrics = FileOperationMetrics(session_id=session_id)

        file_access_counts = defaultdict(int)

        for node in nodes:
            if node.node_type == "assistant":
                for tool_call in node.tool_calls:
                    tool_name = tool_call["name"]
                    tool_input = tool_call.get("input", {})

                    # Extract file operations
                    if tool_name in {
                        "Read",
                        "Write",
                        "Edit",
                        "MultiEdit",
                        "NotebookEdit",
                    }:
                        file_path = tool_input.get("file_path") or tool_input.get(
                            "path", ""
                        )

                        if file_path:
                            file_access_counts[file_path] += 1

                            if tool_name == "Read":
                                metrics.files_read.add(file_path)
                                metrics.operation_counts["read"] = (
                                    metrics.operation_counts.get("read", 0) + 1
                                )
                            elif tool_name == "Write":
                                metrics.files_written.add(file_path)
                                metrics.operation_counts["write"] = (
                                    metrics.operation_counts.get("write", 0) + 1
                                )
                            elif tool_name in {"Edit", "MultiEdit"}:
                                metrics.files_edited.add(file_path)
                                metrics.operation_counts["edit"] = (
                                    metrics.operation_counts.get("edit", 0) + 1
                                )

        # Find file hotspots (most accessed files)
        metrics.file_hotspots = sorted(
            file_access_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Detect edit patterns
        metrics.edit_patterns = self._detect_edit_patterns(nodes)

        return metrics

    def _detect_edit_patterns(self, nodes: List[MessageNode]) -> List[str]:
        """Detect common file editing patterns"""
        patterns = []

        edit_tools = {"Edit", "MultiEdit", "Write"}
        edit_count = 0

        for node in nodes:
            if node.node_type == "assistant":
                for tool_call in node.tool_calls:
                    if tool_call["name"] in edit_tools:
                        edit_count += 1

        if edit_count > 20:
            patterns.append("heavy_editing")
        elif edit_count > 10:
            patterns.append("moderate_editing")
        elif edit_count > 0:
            patterns.append("light_editing")

        return patterns


class SessionMetrics:
    """Calculate comprehensive session statistics and optimization metrics"""

    def calculate_metrics(
        self,
        nodes: List[MessageNode],
        conversation_flow: ConversationFlow,
        tool_usage: ToolUsageMetrics,
        file_operations: FileOperationMetrics,
    ) -> SessionAnalysisReport:
        """Calculate comprehensive session metrics"""

        if not nodes:
            return SessionAnalysisReport(
                session_context=SessionContext("unknown"),
                conversation_flow=conversation_flow,
                tool_usage=tool_usage,
                file_operations=file_operations,
            )

        # Build session context
        session_context = self._build_session_context(nodes)

        # Calculate optimization metrics
        total_tokens = sum(node.token_count for node in nodes)
        optimization_score = self._calculate_optimization_score(
            total_tokens, conversation_flow, tool_usage, file_operations
        )

        complexity_rating = self._determine_complexity(
            total_tokens, len(nodes), tool_usage, file_operations
        )

        recommended_chunks = self._calculate_recommended_chunks(total_tokens)
        cost_estimate = self._estimate_cost(total_tokens)

        # Detect high-level patterns
        patterns_detected = self._detect_session_patterns(
            conversation_flow, tool_usage, file_operations
        )

        return SessionAnalysisReport(
            session_context=session_context,
            conversation_flow=conversation_flow,
            tool_usage=tool_usage,
            file_operations=file_operations,
            optimization_score=optimization_score,
            complexity_rating=complexity_rating,
            recommended_chunks=recommended_chunks,
            cost_estimate=cost_estimate,
            patterns_detected=patterns_detected,
        )

    def _build_session_context(self, nodes: List[MessageNode]) -> SessionContext:
        """Build session context from nodes"""
        session_id = nodes[0].session_id
        created_at = min(node.timestamp for node in nodes)
        ended_at = max(node.timestamp for node in nodes)

        # Try to extract project context from file paths
        project_name = "unknown"
        working_directory = ""

        for node in nodes:
            if node.node_type == "assistant":
                for tool_call in node.tool_calls:
                    if tool_call["name"] in {"Read", "Write", "Edit"}:
                        file_path = tool_call.get("input", {}).get("file_path", "")
                        if file_path and "/master_root/" in file_path:
                            parts = file_path.split("/master_root/")
                            if len(parts) > 1:
                                project_path = parts[1].split("/")[0]
                                if project_path and project_name == "unknown":
                                    project_name = project_path
                                working_directory = (
                                    f"/home/opsvi/master_root/{project_path}"
                                )
                        break

        return SessionContext(
            session_id=session_id,
            project_name=project_name,
            working_directory=working_directory,
            created_at=created_at,
            ended_at=ended_at,
        )

    def _calculate_optimization_score(
        self,
        total_tokens: int,
        conversation_flow: ConversationFlow,
        tool_usage: ToolUsageMetrics,
        file_operations: FileOperationMetrics,
    ) -> float:
        """Calculate optimization score (0-100)"""
        score = 100.0

        # Penalize for large token count
        if total_tokens > 200000:
            score -= 30
        elif total_tokens > 100000:
            score -= 15
        elif total_tokens > 50000:
            score -= 5

        # Reward for structured patterns
        if "structured_planning" in conversation_flow.patterns:
            score += 10

        if "session_continuation" in conversation_flow.patterns:
            score += 5

        # Penalize for excessive tool usage without clear patterns
        tool_count = sum(tool_usage.tool_counts.values())
        if tool_count > 100:
            score -= 10

        # Reward for good tool success rates
        avg_success_rate = (
            statistics.mean(tool_usage.tool_success_rate.values())
            if tool_usage.tool_success_rate
            else 1.0
        )
        score += (avg_success_rate - 0.8) * 25  # Bonus for >80% success

        return max(0, min(100, score))

    def _determine_complexity(
        self,
        total_tokens: int,
        node_count: int,
        tool_usage: ToolUsageMetrics,
        file_operations: FileOperationMetrics,
    ) -> str:
        """Determine session complexity rating"""

        complexity_score = 0

        # Token-based complexity
        if total_tokens > 200000:
            complexity_score += 3
        elif total_tokens > 100000:
            complexity_score += 2
        elif total_tokens > 50000:
            complexity_score += 1

        # Tool usage complexity
        tool_count = sum(tool_usage.tool_counts.values())
        if tool_count > 50:
            complexity_score += 2
        elif tool_count > 20:
            complexity_score += 1

        # File operation complexity
        file_count = len(
            file_operations.files_read
            | file_operations.files_written
            | file_operations.files_edited
        )
        if file_count > 20:
            complexity_score += 2
        elif file_count > 10:
            complexity_score += 1

        # MCP tool usage adds complexity
        if len(tool_usage.mcp_tools_used) > 5:
            complexity_score += 1

        if complexity_score >= 6:
            return "Very High"
        elif complexity_score >= 4:
            return "High"
        elif complexity_score >= 2:
            return "Medium"
        else:
            return "Low"

    def _calculate_recommended_chunks(self, total_tokens: int) -> int:
        """Calculate recommended number of chunks for optimization"""
        if total_tokens <= 10000:
            return 1
        elif total_tokens <= 50000:
            return max(2, total_tokens // 25000)
        else:
            return max(5, total_tokens // 20000)

    def _estimate_cost(self, total_tokens: int) -> float:
        """Estimate cost based on token count (rough approximation)"""
        # Using approximate GPT-4 pricing: $0.025 per 1K tokens
        return (total_tokens / 1000) * 0.025

    def _detect_session_patterns(
        self,
        conversation_flow: ConversationFlow,
        tool_usage: ToolUsageMetrics,
        file_operations: FileOperationMetrics,
    ) -> List[str]:
        """Detect high-level session patterns"""
        patterns = []

        # Copy conversation patterns
        patterns.extend(conversation_flow.patterns)

        # Add tool-based patterns
        if sum(tool_usage.tool_categories.get(cat, 0) for cat in ["file_ops"]) > 20:
            patterns.append("file_intensive")

        if tool_usage.tool_categories.get("web_ops", 0) > 10:
            patterns.append("research_heavy")

        if len(tool_usage.mcp_tools_used) > 3:
            patterns.append("mcp_integration")

        if "TodoWrite" in tool_usage.tool_counts:
            patterns.append("task_oriented")

        # Add file operation patterns
        patterns.extend(file_operations.edit_patterns)

        return list(set(patterns))  # Remove duplicates


class SessionAnalyticsEngine:
    """Main engine for comprehensive session analysis"""

    def __init__(self):
        self.log_parser = LogParser()
        self.conversation_analyzer = ConversationAnalyzer()
        self.tool_analyzer = ToolAnalyzer()
        self.file_analyzer = FileAnalyzer()
        self.session_metrics = SessionMetrics()

    def analyze_session(self, jsonl_path: Path) -> SessionAnalysisReport:
        """Analyze a single session file"""
        print(f"Analyzing session: {jsonl_path}")

        # Parse the session file
        nodes = self.log_parser.parse_session_file(jsonl_path)

        if not nodes:
            print(f"Warning: No valid nodes found in {jsonl_path}")
            return SessionAnalysisReport(
                session_context=SessionContext("unknown"),
                conversation_flow=ConversationFlow("unknown"),
                tool_usage=ToolUsageMetrics("unknown"),
                file_operations=FileOperationMetrics("unknown"),
            )

        # Analyze different aspects
        conversation_flow = self.conversation_analyzer.analyze_conversation(nodes)
        tool_usage = self.tool_analyzer.analyze_tool_usage(nodes)
        file_operations = self.file_analyzer.analyze_file_operations(nodes)

        # Calculate comprehensive metrics
        report = self.session_metrics.calculate_metrics(
            nodes, conversation_flow, tool_usage, file_operations
        )

        return report

    def analyze_directory(
        self, directory_path: Path, pattern: str = "*.jsonl"
    ) -> List[SessionAnalysisReport]:
        """Analyze all session files in a directory"""
        reports = []

        if not directory_path.exists():
            print(f"Directory not found: {directory_path}")
            return reports

        jsonl_files = list(directory_path.glob(pattern))
        print(f"Found {len(jsonl_files)} session files to analyze")

        for jsonl_file in jsonl_files:
            try:
                report = self.analyze_session(jsonl_file)
                reports.append(report)
            except Exception as e:
                print(f"Error analyzing {jsonl_file}: {e}")
                continue

        return reports

    def generate_summary_report(self, reports: List[SessionAnalysisReport]) -> Dict:
        """Generate aggregate summary from multiple session reports"""
        if not reports:
            return {"error": "No reports to summarize"}

        # Aggregate statistics
        total_sessions = len(reports)
        total_tokens = sum(
            sum(node.token_count for node in [])  # Would need to store this
            for report in reports
        )

        avg_optimization_score = statistics.mean(
            report.optimization_score for report in reports
        )

        complexity_distribution = Counter(
            report.complexity_rating for report in reports
        )

        # Pattern analysis
        all_patterns = []
        for report in reports:
            all_patterns.extend(report.patterns_detected)

        pattern_frequency = Counter(all_patterns)

        # Tool usage aggregation
        all_tool_counts = defaultdict(int)
        all_mcp_tools = set()

        for report in reports:
            for tool, count in report.tool_usage.tool_counts.items():
                all_tool_counts[tool] += count
            all_mcp_tools.update(report.tool_usage.mcp_tools_used)

        # Cost and optimization analysis
        total_cost = sum(report.cost_estimate for report in reports)
        optimization_potential = len([r for r in reports if r.optimization_score < 70])

        return {
            "summary": {
                "total_sessions_analyzed": total_sessions,
                "avg_optimization_score": round(avg_optimization_score, 2),
                "total_estimated_cost": round(total_cost, 2),
                "sessions_needing_optimization": optimization_potential,
            },
            "complexity_distribution": dict(complexity_distribution),
            "top_patterns": dict(pattern_frequency.most_common(10)),
            "tool_usage": {
                "top_tools": dict(Counter(all_tool_counts).most_common(10)),
                "mcp_tools_discovered": len(all_mcp_tools),
                "unique_mcp_tools": list(all_mcp_tools),
            },
            "optimization_recommendations": self._generate_optimization_recommendations(
                reports
            ),
        }

    def _generate_optimization_recommendations(
        self, reports: List[SessionAnalysisReport]
    ) -> List[str]:
        """Generate optimization recommendations based on analysis"""
        recommendations = []

        # Analyze high-token sessions
        high_token_sessions = [r for r in reports if r.cost_estimate > 5.0]
        if high_token_sessions:
            recommendations.append(
                f"Consider chunking {len(high_token_sessions)} high-cost sessions "
                f"(avg chunks: {statistics.mean(r.recommended_chunks for r in high_token_sessions):.1f})"
            )

        # Analyze tool success rates
        low_success_sessions = []
        for report in reports:
            if report.tool_usage.tool_success_rate:
                avg_success = statistics.mean(
                    report.tool_usage.tool_success_rate.values()
                )
                if avg_success < 0.8:
                    low_success_sessions.append(report)

        if low_success_sessions:
            recommendations.append(
                f"Investigate tool reliability in {len(low_success_sessions)} sessions "
                f"with <80% success rates"
            )

        # Pattern-based recommendations
        pattern_counts = defaultdict(int)
        for report in reports:
            for pattern in report.patterns_detected:
                pattern_counts[pattern] += 1

        if pattern_counts.get("file_intensive", 0) > len(reports) * 0.3:
            recommendations.append(
                "Consider file operation optimization - detected in 30%+ of sessions"
            )

        if pattern_counts.get("research_heavy", 0) > len(reports) * 0.2:
            recommendations.append(
                "Web research patterns detected - consider caching strategies"
            )

        return recommendations


def main():
    """Example usage of SessionAnalyticsEngine"""
    engine = SessionAnalyticsEngine()

    # Analyze Claude projects directory
    claude_projects = Path("/home/opsvi/.claude/projects/-home-opsvi-master-root")

    if claude_projects.exists():
        print("Analyzing Claude session files...")
        reports = engine.analyze_directory(claude_projects)

        if reports:
            # Generate summary
            summary = engine.generate_summary_report(reports)

            # Save results
            output_dir = Path("/home/opsvi/master_root/apps/session-optimizer")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save detailed reports
            with open(output_dir / "detailed_session_analysis.json", "w") as f:
                json.dump(
                    [
                        {
                            "session_id": r.session_context.session_id,
                            "project_name": r.session_context.project_name,
                            "optimization_score": r.optimization_score,
                            "complexity_rating": r.complexity_rating,
                            "cost_estimate": r.cost_estimate,
                            "patterns": r.patterns_detected,
                            "tool_counts": r.tool_usage.tool_counts,
                            "file_operations": {
                                "files_read": len(r.file_operations.files_read),
                                "files_written": len(r.file_operations.files_written),
                                "files_edited": len(r.file_operations.files_edited),
                            },
                        }
                        for r in reports
                    ],
                    f,
                    indent=2,
                    default=str,
                )

            # Save summary
            with open(output_dir / "session_analysis_summary.json", "w") as f:
                json.dump(summary, f, indent=2, default=str)

            print(f"\nAnalysis complete!")
            print(f"Sessions analyzed: {len(reports)}")
            print(
                f"Average optimization score: {summary['summary']['avg_optimization_score']}"
            )
            print(
                f"Total estimated cost: ${summary['summary']['total_estimated_cost']:.2f}"
            )
            print(
                f"Sessions needing optimization: {summary['summary']['sessions_needing_optimization']}"
            )
            print(f"Results saved to: {output_dir}")
        else:
            print("No session files found to analyze")
    else:
        print(f"Claude projects directory not found: {claude_projects}")


if __name__ == "__main__":
    main()
