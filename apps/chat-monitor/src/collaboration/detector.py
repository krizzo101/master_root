"""
Collaboration Detection Engine

Advanced pattern recognition system that identifies agent collaboration events
from chat log entries. Goes beyond basic tool usage to detect meaningful
inter-agent communication, coordination, and handoff patterns.
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class CollaborationEvent:
    """Represents a detected collaboration event between agents."""

    event_type: str
    timestamp: float
    primary_session: str
    partner_session: Optional[str] = None
    significance: int = 0  # 1-10 scale
    details: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)


class CollaborationDetector:
    """
    Detects and classifies agent collaboration patterns from log entries.

    Identifies:
    - Direct agent spawning and task delegation
    - Shared workspace coordination (multiple agents, same files)
    - Communication patterns through tool parameters
    - Task handoff chains and dependencies
    - Workspace conflicts and resolution attempts
    """

    def __init__(self, settings):
        self.settings = settings

        # Pattern tracking for cross-session analysis
        self.session_contexts: Dict[str, Dict] = {}
        self.file_access_timeline: List[
            Tuple[float, str, str, str]
        ] = []  # time, session, action, file
        self.agent_spawn_network: Dict[str, List[str]] = {}  # parent -> children
        self.communication_sequences: Dict[str, List[Dict]] = {}

        # Collaboration detection patterns
        self.collaboration_patterns = {
            "agent_spawn": self._detect_agent_spawn,
            "workspace_coordination": self._detect_workspace_coordination,
            "task_handoff": self._detect_task_handoff,
            "shared_data_access": self._detect_shared_data_access,
            "error_collaboration": self._detect_error_collaboration,
            "message_passing": self._detect_message_passing,
        }

        # Cache for recent analysis to improve performance
        self.recent_events_cache: Dict[str, List[CollaborationEvent]] = {}

    async def analyze_entry(
        self, session_id: str, entry: Dict
    ) -> List[CollaborationEvent]:
        """
        Analyze a single log entry for collaboration patterns.

        Args:
            session_id: ID of the session this entry belongs to
            entry: Parsed JSON log entry

        Returns:
            List of detected collaboration events
        """
        events = []

        # Update session context
        await self._update_session_context(session_id, entry)

        # Run all collaboration pattern detectors
        for pattern_name, detector_func in self.collaboration_patterns.items():
            try:
                pattern_events = await detector_func(session_id, entry)
                if pattern_events:
                    events.extend(pattern_events)
            except Exception as e:
                # Log error but continue with other detectors
                if self.settings.verbose:
                    print(f"Error in {pattern_name} detector: {e}")

        # Cache recent events for this session
        if session_id not in self.recent_events_cache:
            self.recent_events_cache[session_id] = []

        self.recent_events_cache[session_id].extend(events)

        # Keep only recent events in cache
        cutoff_time = datetime.now().timestamp() - self.settings.recent_events_window
        self.recent_events_cache[session_id] = [
            event
            for event in self.recent_events_cache[session_id]
            if event.timestamp >= cutoff_time
        ]

        return events

    async def _update_session_context(self, session_id: str, entry: Dict):
        """Update context tracking for a session."""
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {
                "tools_used": [],
                "files_accessed": set(),
                "recent_messages": [],
                "spawn_events": [],
                "last_activity": datetime.now().timestamp(),
            }

        context = self.session_contexts[session_id]
        context["last_activity"] = datetime.now().timestamp()

        # Track message content for communication analysis
        message = entry.get("message", {})
        if message:
            context["recent_messages"].append(
                {
                    "timestamp": entry.get("timestamp", ""),
                    "type": entry.get("type", ""),
                    "content": message,
                }
            )

            # Keep only recent messages
            cutoff_time = datetime.now().timestamp() - 300  # 5 minutes
            context["recent_messages"] = [
                msg
                for msg in context["recent_messages"]
                if self._parse_timestamp(msg["timestamp"]) >= cutoff_time
            ]

    async def _detect_agent_spawn(
        self, session_id: str, entry: Dict
    ) -> List[CollaborationEvent]:
        """Detect agent spawning events (Task tool, claude-code-wrapper, etc.)."""
        events = []

        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            return events

        for item in content:
            if not isinstance(item, dict) or "name" not in item:
                continue

            tool_name = item["name"]
            tool_input = item.get("input", {})

            if tool_name == "Task":
                # Direct agent spawning via Task tool
                agent_type = tool_input.get("subagent_type", "unknown")
                description = tool_input.get("description", "")

                event = CollaborationEvent(
                    event_type="agent_spawn",
                    timestamp=self._parse_timestamp(entry.get("timestamp")),
                    primary_session=session_id,
                    significance=7,  # High significance for direct spawning
                    details={
                        "spawn_method": "Task",
                        "agent_type": agent_type,
                        "task_description": description[:100],
                    },
                    evidence=[f"Task tool with subagent_type: {agent_type}"],
                )
                events.append(event)

                # Track spawn network
                if session_id not in self.agent_spawn_network:
                    self.agent_spawn_network[session_id] = []
                self.agent_spawn_network[session_id].append(agent_type)

            elif "claude-code-wrapper" in tool_name:
                # Claude Code wrapper spawning
                task_desc = tool_input.get("task", "")
                is_async = "async" in tool_name

                event = CollaborationEvent(
                    event_type="agent_spawn",
                    timestamp=self._parse_timestamp(entry.get("timestamp")),
                    primary_session=session_id,
                    significance=6,  # Medium-high significance
                    details={
                        "spawn_method": "claude_code_wrapper",
                        "task_description": task_desc[:100],
                        "async_execution": is_async,
                    },
                    evidence=[f"Claude Code wrapper: {tool_name}"],
                )
                events.append(event)

        return events

    async def _detect_workspace_coordination(
        self, session_id: str, entry: Dict
    ) -> List[CollaborationEvent]:
        """Detect shared workspace coordination and potential conflicts."""
        events = []

        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            return events

        current_time = self._parse_timestamp(entry.get("timestamp"))

        for item in content:
            if not isinstance(item, dict) or "name" not in item:
                continue

            tool_name = item["name"]
            tool_input = item.get("input", {})

            # Track file operations
            file_paths = []

            if tool_name in ["Read", "Write", "Edit"]:
                file_path = tool_input.get("file_path")
                if file_path:
                    file_paths.append(file_path)

            elif tool_name == "MultiEdit":
                edits = tool_input.get("edits", [])
                for edit in edits:
                    if isinstance(edit, dict) and "file_path" in edit:
                        file_paths.append(edit["file_path"])

            # Record file access and check for coordination patterns
            for file_path in file_paths:
                self.file_access_timeline.append(
                    (current_time, session_id, tool_name, file_path)
                )

                # Check for recent access by other sessions (coordination/conflict)
                recent_access = [
                    (timestamp, other_session, action, path)
                    for timestamp, other_session, action, path in self.file_access_timeline
                    if path == file_path
                    and other_session != session_id
                    and current_time - timestamp
                    <= self.settings.workspace_conflict_threshold
                ]

                if recent_access:
                    # Detected workspace coordination
                    for timestamp, other_session, action, path in recent_access:
                        significance = self._calculate_coordination_significance(
                            tool_name, action, current_time - timestamp
                        )

                        event = CollaborationEvent(
                            event_type="workspace_coordination",
                            timestamp=current_time,
                            primary_session=session_id,
                            partner_session=other_session,
                            significance=significance,
                            details={
                                "file_path": file_path,
                                "current_action": tool_name,
                                "other_action": action,
                                "time_delta": current_time - timestamp,
                                "conflict_potential": self._assess_conflict_potential(
                                    tool_name, action
                                ),
                            },
                            evidence=[
                                f"File {file_path} accessed by {session_id} ({tool_name}) "
                                f"and {other_session} ({action}) within {current_time - timestamp:.1f}s"
                            ],
                        )
                        events.append(event)

        # Cleanup old file access records
        cutoff_time = current_time - (self.settings.workspace_conflict_threshold * 5)
        self.file_access_timeline = [
            record for record in self.file_access_timeline if record[0] >= cutoff_time
        ]

        return events

    async def _detect_task_handoff(
        self, session_id: str, entry: Dict
    ) -> List[CollaborationEvent]:
        """Detect task handoff patterns between agents."""
        events = []

        # Look for patterns indicating task handoffs:
        # 1. Agent spawn followed by specific file access
        # 2. Error handling delegation
        # 3. Completion status communication

        message = entry.get("message", {})
        content = message.get("content", [])

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "name" in item:
                    tool_name = item["name"]

                    # Check if this looks like a handoff completion
                    if (
                        tool_name in ["mcp__knowledge__knowledge_store"]
                        and session_id in self.agent_spawn_network
                    ):
                        # Agent storing knowledge after completing work - potential handoff completion
                        spawned_agents = self.agent_spawn_network[session_id]
                        if spawned_agents:
                            event = CollaborationEvent(
                                event_type="task_handoff_completion",
                                timestamp=self._parse_timestamp(entry.get("timestamp")),
                                primary_session=session_id,
                                significance=5,
                                details={
                                    "completion_method": "knowledge_store",
                                    "spawned_agents": spawned_agents[
                                        -3:
                                    ],  # Last 3 spawned
                                },
                                evidence=["Knowledge storage after agent spawning"],
                            )
                            events.append(event)

        # Check message content for handoff keywords
        if entry.get("type") == "assistant":
            text_content = self._extract_text_content(message)
            handoff_keywords = [
                "handoff",
                "taking over",
                "continue with",
                "next agent",
                "delegation",
                "passing to",
                "coordinating with",
            ]

            if any(keyword in text_content.lower() for keyword in handoff_keywords):
                event = CollaborationEvent(
                    event_type="task_handoff_communication",
                    timestamp=self._parse_timestamp(entry.get("timestamp")),
                    primary_session=session_id,
                    significance=4,
                    details={
                        "communication_method": "text_message",
                        "content_preview": text_content[:100],
                    },
                    evidence=["Handoff keywords detected in message"],
                )
                events.append(event)

        return events

    async def _detect_shared_data_access(
        self, session_id: str, entry: Dict
    ) -> List[CollaborationEvent]:
        """Detect shared data access patterns indicating collaboration."""
        events = []

        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            return events

        for item in content:
            if not isinstance(item, dict) or "name" not in item:
                continue

            tool_name = item["name"]
            tool_input = item.get("input", {})

            # Look for shared data access patterns
            if tool_name == "mcp__knowledge__knowledge_query":
                # Knowledge base queries indicate potential data sharing
                query_text = tool_input.get("search_text", "")
                query_type = tool_input.get("query_type", "")

                if query_text and len(query_text) > 10:  # Meaningful queries only
                    event = CollaborationEvent(
                        event_type="shared_data_access",
                        timestamp=self._parse_timestamp(entry.get("timestamp")),
                        primary_session=session_id,
                        significance=3,
                        details={
                            "data_type": "knowledge_base",
                            "query_type": query_type,
                            "query_text": query_text[:50],
                        },
                        evidence=[f"Knowledge query: {query_text}"],
                    )
                    events.append(event)

        return events

    async def _detect_error_collaboration(
        self, session_id: str, entry: Dict
    ) -> List[CollaborationEvent]:
        """Detect error handling collaboration between agents."""
        events = []

        # Look for error messages that might trigger collaboration
        if entry.get("type") == "user":
            message = entry.get("message", {})
            content_str = str(message.get("content", ""))

            error_indicators = ["error", "failed", "exception", "timeout", "blocked"]
            if any(indicator in content_str.lower() for indicator in error_indicators):
                event = CollaborationEvent(
                    event_type="error_collaboration",
                    timestamp=self._parse_timestamp(entry.get("timestamp")),
                    primary_session=session_id,
                    significance=6,  # Errors are significant for collaboration
                    details={
                        "error_context": content_str[:100],
                        "collaboration_trigger": "error_handling",
                    },
                    evidence=["Error message detected"],
                )
                events.append(event)

        return events

    async def _detect_message_passing(
        self, session_id: str, entry: Dict
    ) -> List[CollaborationEvent]:
        """Detect message passing patterns between agents."""
        events = []

        # This is a placeholder for more advanced message passing detection
        # Would require integration with collaboration infrastructure
        # For now, detect potential message passing through tool parameters

        message = entry.get("message", {})
        content = message.get("content", [])

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "name" in item:
                    tool_name = item["name"]
                    tool_input = item.get("input", {})

                    # Look for tools that might facilitate message passing
                    if "mcp__" in tool_name and "message" in str(tool_input).lower():
                        event = CollaborationEvent(
                            event_type="potential_message_passing",
                            timestamp=self._parse_timestamp(entry.get("timestamp")),
                            primary_session=session_id,
                            significance=3,
                            details={
                                "tool_name": tool_name,
                                "message_indication": True,
                            },
                            evidence=["MCP tool with message-like parameters"],
                        )
                        events.append(event)

        return events

    def _calculate_coordination_significance(
        self, current_action: str, other_action: str, time_delta: float
    ) -> int:
        """Calculate significance score for workspace coordination events."""
        base_significance = 3

        # Higher significance for write operations
        if current_action in ["Write", "Edit", "MultiEdit"] or other_action in [
            "Write",
            "Edit",
            "MultiEdit",
        ]:
            base_significance += 2

        # Higher significance for very close timing
        if time_delta < 1.0:  # Within 1 second
            base_significance += 3
        elif time_delta < 5.0:  # Within 5 seconds
            base_significance += 2

        # Conflicting operations get higher significance
        if self._assess_conflict_potential(current_action, other_action) == "high":
            base_significance += 2

        return min(base_significance, 10)  # Cap at 10

    def _assess_conflict_potential(self, action1: str, action2: str) -> str:
        """Assess potential for conflict between two file operations."""
        write_operations = {"Write", "Edit", "MultiEdit"}

        if action1 in write_operations and action2 in write_operations:
            return "high"  # Two writes could conflict
        elif (action1 in write_operations and action2 == "Read") or (
            action2 in write_operations and action1 == "Read"
        ):
            return "medium"  # Read during write might be stale
        else:
            return "low"  # Multiple reads are safe

    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Parse timestamp string to float seconds since epoch."""
        if not timestamp_str:
            return datetime.now().timestamp()

        try:
            # Handle ISO format timestamps
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.timestamp()
        except (ValueError, AttributeError):
            return datetime.now().timestamp()

    def _extract_text_content(self, message: Dict) -> str:
        """Extract text content from message structure."""
        content = message.get("content", [])

        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if "text" in item:
                        text_parts.append(item["text"])
                    elif "content" in item and isinstance(item["content"], str):
                        text_parts.append(item["content"])
                elif isinstance(item, str):
                    text_parts.append(item)
            return " ".join(text_parts)

        return str(content)
