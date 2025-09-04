#!/usr/bin/env python3
"""
Agent Log Parser for Real-Time Monitoring
Specialized log parser that provides structured analysis of agent execution logs
"""

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add chat-search to path
sys.path.append(str(Path(__file__).parent.parent.parent / "chat-search"))
from chat_search import ChatSearcher

from .agent_monitor import ErrorInfo, ProgressStatus


class AgentLogParser:
    """
    Specialized parser for extracting structured information from agent logs
    Uses chat_search.py as the foundation for log analysis
    """

    def __init__(self, chat_logs_dir: str = None):
        """
        Initialize the log parser

        Args:
            chat_logs_dir: Directory containing chat logs
        """
        if chat_logs_dir is None:
            # Default to Claude projects directory
            chat_logs_dir = (
                Path.home()
                / ".claude"
                / "projects"
                / f"-home-opsvi-master-root-apps-agent-orchestrator"
            )

        self.chat_logs_dir = Path(chat_logs_dir)
        self.searcher = ChatSearcher(str(self.chat_logs_dir))

        # Patterns for different types of analysis
        self.error_patterns = [
            r"error:\s*(.+)",
            r"exception:\s*(.+)",
            r"failed:\s*(.+)",
            r"traceback.*?(\w+error:\s*.+)",
            r"errno\s*(\d+):\s*(.+)",
        ]

        self.progress_patterns = [
            r"(?:task|step)\s*(\d+)(?:\s*of\s*(\d+))?",
            r"progress:\s*(\d+)%",
            r"completed:\s*(.+)",
            r"starting:\s*(.+)",
            r"executing:\s*(.+)",
        ]

        self.deliverable_patterns = [
            r'(?:created|generated|wrote|saved)\s+(?:file\s+)?["\']?([^"\'\s]+\.[a-zA-Z0-9]+)',
            r'output:\s*([^"\'\s]+\.[a-zA-Z0-9]+)',
            r"deliverable:\s*(.+)",
        ]

    async def parse_agent_progress(self, uuid: str) -> ProgressStatus:
        """
        Parse agent progress from logs

        Args:
            uuid: Agent UUID to analyze

        Returns:
            ProgressStatus with extracted progress information
        """
        progress = ProgressStatus()

        try:
            # Search for progress-related entries
            progress_results = self.searcher.search(
                query=r"(?i)(progress|completed|task|step|executing|starting)",
                files_filter=[f"{uuid}.jsonl"],
                limit=100,
                context=False,
            )

            if not progress_results:
                return progress

            # Sort by timestamp
            progress_results.sort(key=lambda x: x.get("timestamp", ""))

            completed_tasks = set()
            current_task = ""
            progress_percentage = 0.0

            for entry in progress_results:
                content = str(entry.get("full_content", "")).lower()
                timestamp = entry.get("timestamp", "")

                # Extract current task
                for pattern in self.progress_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            if len(match) >= 2 and match[1]:
                                # Progress with numbers (e.g., "task 3 of 10")
                                try:
                                    current_num = int(match[0])
                                    total_num = int(match[1])
                                    progress_percentage = (
                                        current_num / total_num
                                    ) * 100
                                    current_task = f"Task {current_num} of {total_num}"
                                except ValueError:
                                    pass
                            else:
                                current_task = str(match[0]) if match[0] else ""
                        else:
                            if match.endswith("%"):
                                # Direct percentage
                                try:
                                    progress_percentage = float(match[:-1])
                                except ValueError:
                                    pass
                            else:
                                current_task = str(match)

                # Look for completion indicators
                if any(
                    indicator in content
                    for indicator in ["completed", "finished", "done", "✓", "success"]
                ):
                    # Extract what was completed
                    lines = content.split("\n")
                    for line in lines:
                        if any(
                            indicator in line
                            for indicator in ["completed", "finished", "done"]
                        ):
                            completed_tasks.add(line.strip()[:100])
                            break

                progress.last_activity = timestamp

            progress.completed_tasks = list(completed_tasks)
            progress.current_task = current_task
            progress.progress_percentage = min(progress_percentage, 100.0)

            # Estimate completion time if we have progress data
            if progress_percentage > 0 and progress_percentage < 100:
                try:
                    # Very rough estimation based on current progress
                    if progress.last_activity:
                        last_time = datetime.fromisoformat(
                            progress.last_activity.replace("Z", "+00:00")
                        )
                        remaining_percent = 100 - progress_percentage
                        # Estimate based on time per percent completed
                        estimated_remaining = timedelta(
                            minutes=remaining_percent * 2
                        )  # 2 min per percent (rough)
                        estimated_completion = last_time + estimated_remaining
                        progress.estimated_completion = estimated_completion.isoformat()
                except:
                    pass

        except Exception as e:
            print(f"Error parsing progress for {uuid}: {e}")

        return progress

    async def detect_agent_errors(self, uuid: str) -> List[ErrorInfo]:
        """
        Detect and categorize errors from agent logs

        Args:
            uuid: Agent UUID to analyze

        Returns:
            List of ErrorInfo objects describing detected errors
        """
        errors = []

        try:
            # Search for error-related entries
            error_results = self.searcher.search(
                query=r"(?i)(error|exception|failed|traceback|errno)",
                files_filter=[f"{uuid}.jsonl"],
                limit=200,
                context=True,  # Get context for better error analysis
            )

            for entry in error_results:
                content = str(entry.get("full_content", ""))
                timestamp = entry.get("timestamp", "")
                context_info = entry.get("context", {})

                # Categorize the error
                error_type = "unknown_error"
                error_message = ""
                severity = "warning"

                for pattern in self.error_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        if isinstance(matches[0], tuple):
                            error_message = matches[0][
                                -1
                            ]  # Get the last group (the actual message)
                        else:
                            error_message = matches[0]
                        break

                # Determine error type and severity
                content_lower = content.lower()

                if "traceback" in content_lower or "exception" in content_lower:
                    error_type = "python_exception"
                    severity = "error"
                elif "failed to" in content_lower:
                    error_type = "operation_failure"
                    severity = "error"
                elif "timeout" in content_lower:
                    error_type = "timeout_error"
                    severity = "warning"
                elif "permission" in content_lower or "access" in content_lower:
                    error_type = "permission_error"
                    severity = "error"
                elif (
                    "file not found" in content_lower or "no such file" in content_lower
                ):
                    error_type = "file_not_found"
                    severity = "warning"
                elif "connection" in content_lower or "network" in content_lower:
                    error_type = "network_error"
                    severity = "warning"
                elif "syntax error" in content_lower:
                    error_type = "syntax_error"
                    severity = "error"

                # Extract context from surrounding messages
                context_str = ""
                if context_info.get("prev_message"):
                    context_str = f"Previous: {context_info['prev_message'][:100]}"

                error = ErrorInfo(
                    timestamp=timestamp,
                    error_type=error_type,
                    error_message=error_message[:300]
                    if error_message
                    else content[:300],
                    context=context_str,
                    severity=severity,
                )

                errors.append(error)

        except Exception as e:
            print(f"Error detecting errors for {uuid}: {e}")

        return errors

    async def check_context_usage(self, uuid: str) -> float:
        """
        Estimate context usage based on log analysis

        Args:
            uuid: Agent UUID to analyze

        Returns:
            Estimated context usage as a percentage (0.0 to 100.0)
        """
        try:
            # Get all log entries for the agent
            all_results = self.searcher.search(
                query=r".*",  # Match everything
                files_filter=[f"{uuid}.jsonl"],
                limit=10000,  # Get all entries
                context=False,
            )

            if not all_results:
                return 0.0

            # Estimate context usage based on:
            # 1. Total number of messages
            # 2. Average message length
            # 3. Tool usage frequency

            total_messages = len(all_results)
            total_content_length = 0
            tool_usage_count = 0

            for entry in all_results:
                content = str(entry.get("full_content", ""))
                total_content_length += len(content)

                # Count tool usage (higher context consumption)
                if any(
                    indicator in content.lower()
                    for indicator in [
                        '"tool_use"',
                        '"tool_result"',
                        "function_calls",
                        "parameters",
                    ]
                ):
                    tool_usage_count += 1

            # Rough estimation formula
            # Assume average Claude context window is ~200k tokens
            # Rough estimate: 4 chars per token
            estimated_tokens = total_content_length / 4

            # Add weight for tool usage (tools consume more context)
            estimated_tokens += tool_usage_count * 500  # 500 tokens per tool use

            # Estimate percentage of 200k context window
            context_percentage = min((estimated_tokens / 200000) * 100, 100.0)

            return context_percentage

        except Exception as e:
            print(f"Error checking context usage for {uuid}: {e}")
            return 0.0

    async def get_agent_deliverables(self, uuid: str) -> List[str]:
        """
        Extract list of deliverables produced by the agent

        Args:
            uuid: Agent UUID to analyze

        Returns:
            List of deliverables (files, outputs, etc.)
        """
        deliverables = []

        try:
            # Search for deliverable-related entries
            deliverable_results = self.searcher.search(
                query=r"(?i)(created|generated|wrote|saved|output|file)",
                files_filter=[f"{uuid}.jsonl"],
                limit=500,
                context=False,
            )

            for entry in deliverable_results:
                content = str(entry.get("full_content", ""))

                # Extract deliverable information
                for pattern in self.deliverable_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, str) and match.strip():
                            deliverable = match.strip()
                            # Clean up the deliverable name
                            deliverable = deliverable.replace('"', "").replace("'", "")
                            if deliverable and deliverable not in deliverables:
                                deliverables.append(deliverable)

                # Also look for explicit deliverable mentions
                if "deliverable:" in content.lower():
                    lines = content.split("\n")
                    for line in lines:
                        if "deliverable:" in line.lower():
                            deliverable = line.split(":", 1)[1].strip()
                            if deliverable and deliverable not in deliverables:
                                deliverables.append(deliverable[:100])  # Limit length

        except Exception as e:
            print(f"Error getting deliverables for {uuid}: {e}")

        return deliverables

    async def analyze_agent_performance(self, uuid: str) -> Dict[str, Any]:
        """
        Comprehensive performance analysis of an agent

        Args:
            uuid: Agent UUID to analyze

        Returns:
            Dictionary with performance metrics
        """
        performance = {
            "total_messages": 0,
            "messages_per_minute": 0.0,
            "tool_usage_frequency": 0,
            "error_rate": 0.0,
            "response_times": [],
            "most_active_periods": [],
            "efficiency_score": 0.0,
        }

        try:
            # Get all log entries
            all_results = self.searcher.search(
                query=r".*", files_filter=[f"{uuid}.jsonl"], limit=10000, context=False
            )

            if not all_results:
                return performance

            # Sort by timestamp
            all_results.sort(key=lambda x: x.get("timestamp", ""))

            performance["total_messages"] = len(all_results)

            # Calculate timing metrics
            timestamps = []
            tool_uses = 0
            errors = 0

            for entry in all_results:
                timestamp_str = entry.get("timestamp", "")
                content = str(entry.get("full_content", "")).lower()

                if timestamp_str:
                    try:
                        ts = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                        timestamps.append(ts)
                    except:
                        continue

                # Count tool usage
                if any(
                    indicator in content
                    for indicator in ["tool_use", "tool_result", "function_calls"]
                ):
                    tool_uses += 1

                # Count errors
                if any(
                    indicator in content
                    for indicator in ["error", "exception", "failed", "traceback"]
                ):
                    errors += 1

            if timestamps:
                # Calculate messages per minute
                total_duration = (timestamps[-1] - timestamps[0]).total_seconds() / 60
                if total_duration > 0:
                    performance["messages_per_minute"] = (
                        len(timestamps) / total_duration
                    )

                # Calculate response times (time between consecutive messages)
                response_times = []
                for i in range(1, len(timestamps)):
                    delta = (timestamps[i] - timestamps[i - 1]).total_seconds()
                    if delta < 300:  # Ignore gaps > 5 minutes
                        response_times.append(delta)

                performance["response_times"] = response_times

            performance["tool_usage_frequency"] = tool_uses
            performance["error_rate"] = (
                (errors / len(all_results)) * 100 if all_results else 0.0
            )

            # Calculate efficiency score (subjective metric)
            # Higher score = more deliverables, fewer errors, consistent activity
            deliverables = await self.get_agent_deliverables(uuid)
            progress = await self.parse_agent_progress(uuid)

            efficiency_score = 0.0
            efficiency_score += len(deliverables) * 20  # 20 points per deliverable
            efficiency_score += (
                progress.progress_percentage * 0.5
            )  # Progress contribution
            efficiency_score -= performance["error_rate"] * 2  # Penalty for errors
            efficiency_score += min(
                performance["messages_per_minute"] * 10, 50
            )  # Activity bonus

            performance["efficiency_score"] = max(0.0, min(efficiency_score, 100.0))

        except Exception as e:
            print(f"Error analyzing performance for {uuid}: {e}")

        return performance


# Example usage
async def example_usage():
    """Example of how to use the AgentLogParser"""

    parser = AgentLogParser()

    # Example UUID
    test_uuid = "team-phase1-001-monitor-1725408000"

    print(f"Analyzing agent: {test_uuid}")

    # Parse progress
    progress = await parser.parse_agent_progress(test_uuid)
    print(f"Progress: {progress.progress_percentage}%")
    print(f"Current task: {progress.current_task}")
    print(f"Completed tasks: {len(progress.completed_tasks)}")

    # Detect errors
    errors = await parser.detect_agent_errors(test_uuid)
    print(f"Errors found: {len(errors)}")
    for error in errors[:3]:  # Show first 3 errors
        print(f"  {error.error_type}: {error.error_message[:100]}")

    # Check context usage
    context_usage = await parser.check_context_usage(test_uuid)
    print(f"Context usage: {context_usage:.1f}%")

    # Get deliverables
    deliverables = await parser.get_agent_deliverables(test_uuid)
    print(f"Deliverables: {deliverables}")

    # Performance analysis
    performance = await parser.analyze_agent_performance(test_uuid)
    print(f"Efficiency score: {performance['efficiency_score']:.1f}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
