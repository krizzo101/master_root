#!/usr/bin/env python3
"""
Claude Code Session Context Extractor
Extracts relevant context from session logs
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from session_detector import SessionDetector


class SessionContext:
    def __init__(self, session_id=None):
        self.detector = SessionDetector()

        if not session_id:
            session_id, _, _ = self.detector.get_current_session_id()

        self.session_id = session_id
        self.session_file = self.detector.get_session_file_path(session_id)

    def get_recent_context(self, num_lines=200, filter_types=None):
        """
        Get recent context from session

        Args:
            num_lines: Number of recent lines to retrieve
            filter_types: List of entry types to include (user, assistant, tool_use, etc.)

        Returns:
            List of context entries
        """
        if not self.session_file or not self.session_file.exists():
            return []

        entries = []
        with open(self.session_file, "r") as f:
            lines = f.readlines()

        # Get last N lines
        recent_lines = lines[-num_lines:] if len(lines) > num_lines else lines

        for line in recent_lines:
            try:
                entry = json.loads(line)

                # Determine entry type
                entry_type = self._get_entry_type(entry)

                # Apply filter if specified
                if filter_types and entry_type not in filter_types:
                    continue

                # Extract relevant fields
                context_entry = {
                    "type": entry_type,
                    "timestamp": entry.get("timestamp") or entry.get("created_at"),
                }

                # Extract content based on type
                if entry_type == "user":
                    context_entry["content"] = entry.get("prompt", "")
                elif entry_type == "assistant":
                    context_entry["content"] = self._extract_assistant_content(entry)
                elif entry_type == "tool_use":
                    context_entry["tool"] = entry.get("tool_name", "")
                    context_entry["input"] = entry.get("tool_input", {})
                elif entry_type == "tool_result":
                    context_entry["output"] = entry.get("tool_output", "")[
                        :500
                    ]  # Truncate
                elif entry_type == "error":
                    context_entry["error"] = entry.get("error", "")

                entries.append(context_entry)

            except json.JSONDecodeError:
                continue

        return entries

    def get_conversation_pairs(self, num_pairs=10):
        """Get recent user-assistant conversation pairs"""
        entries = self.get_recent_context(num_lines=num_pairs * 20)

        pairs = []
        current_user = None

        for entry in entries:
            if entry["type"] == "user":
                current_user = entry
            elif entry["type"] == "assistant" and current_user:
                pairs.append(
                    {
                        "user": current_user["content"],
                        "assistant": entry["content"][:500],  # Truncate
                        "timestamp": entry["timestamp"],
                    }
                )
                current_user = None

        return pairs[-num_pairs:]

    def get_tool_usage(self, num_recent=50):
        """Get recent tool usage patterns"""
        entries = self.get_recent_context(
            num_lines=num_recent * 5, filter_types=["tool_use"]
        )

        tool_usage = {}
        for entry in entries:
            tool = entry.get("tool", "unknown")
            if tool not in tool_usage:
                tool_usage[tool] = []

            tool_usage[tool].append(
                {"timestamp": entry.get("timestamp"), "input": entry.get("input", {})}
            )

        return tool_usage

    def get_code_changes(self, num_recent=20):
        """Extract recent code changes from Edit/Write tools"""
        entries = self.get_recent_context(num_lines=num_recent * 10)

        code_changes = []
        for entry in entries:
            if entry["type"] == "tool_use":
                tool = entry.get("tool", "")
                if tool in ["Edit", "Write", "MultiEdit"]:
                    change = {
                        "tool": tool,
                        "timestamp": entry.get("timestamp"),
                        "file": entry.get("input", {}).get("file_path", ""),
                    }

                    if tool == "Edit":
                        change["old"] = entry.get("input", {}).get("old_string", "")[
                            :100
                        ]
                        change["new"] = entry.get("input", {}).get("new_string", "")[
                            :100
                        ]
                    elif tool == "Write":
                        content = entry.get("input", {}).get("content", "")
                        change["preview"] = content[:200] if content else ""

                    code_changes.append(change)

        return code_changes

    def get_errors(self, num_recent=20):
        """Extract recent errors and their resolutions"""
        entries = self.get_recent_context(num_lines=num_recent * 20)

        errors = []
        current_error = None

        for entry in entries:
            if entry["type"] == "error" or (
                entry["type"] == "tool_result"
                and "error" in entry.get("output", "").lower()
            ):
                current_error = {
                    "timestamp": entry.get("timestamp"),
                    "error": entry.get("error") or entry.get("output", "")[:200],
                    "resolution": None,
                }
                errors.append(current_error)

            elif current_error and entry["type"] == "assistant":
                # Check if assistant provided a resolution
                content = entry.get("content", "")
                if any(
                    word in content.lower()
                    for word in ["fixed", "resolved", "corrected"]
                ):
                    current_error["resolution"] = content[:200]
                    current_error = None

        return errors

    def get_summary_context(self):
        """Get a summary of the session for context"""
        recent = self.get_recent_context(num_lines=500)

        summary = {
            "session_id": self.session_id,
            "total_entries": len(recent),
            "user_prompts": sum(1 for e in recent if e["type"] == "user"),
            "assistant_responses": sum(1 for e in recent if e["type"] == "assistant"),
            "tools_used": len(
                set(e.get("tool", "") for e in recent if e["type"] == "tool_use")
            ),
            "errors": sum(1 for e in recent if e["type"] == "error"),
        }

        # Get unique files modified
        files = set()
        for entry in recent:
            if entry["type"] == "tool_use" and entry.get("tool") in ["Edit", "Write"]:
                file_path = entry.get("input", {}).get("file_path")
                if file_path:
                    files.add(file_path)
        summary["files_modified"] = list(files)

        # Get main topics from user prompts
        prompts = [
            e["content"] for e in recent if e["type"] == "user" and e.get("content")
        ]
        summary["recent_topics"] = prompts[-5:] if prompts else []

        return summary

    def _get_entry_type(self, entry):
        """Determine the type of a session entry"""
        if "role" in entry:
            return entry["role"]
        elif "tool_name" in entry:
            return "tool_use"
        elif "tool_output" in entry:
            return "tool_result"
        elif "error" in entry:
            return "error"
        elif "type" in entry:
            return entry["type"]
        else:
            return "unknown"

    def _extract_assistant_content(self, entry):
        """Extract text content from assistant entry"""
        content = entry.get("content", "")

        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Handle structured content
            text_parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                elif isinstance(item, str):
                    text_parts.append(item)
            return " ".join(text_parts)
        else:
            return str(content)

    def export_context(self, output_file=None):
        """Export session context to file"""
        context = {
            "session_id": self.session_id,
            "exported_at": datetime.now().isoformat(),
            "summary": self.get_summary_context(),
            "recent_conversations": self.get_conversation_pairs(5),
            "tool_usage": self.get_tool_usage(20),
            "code_changes": self.get_code_changes(10),
            "errors": self.get_errors(10),
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(context, f, indent=2)
        else:
            return context


def main():
    """CLI interface for context extraction"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Code Session Context Extractor"
    )
    parser.add_argument(
        "command",
        choices=[
            "recent",
            "conversation",
            "tools",
            "changes",
            "errors",
            "summary",
            "export",
        ],
        help="Command to run",
    )
    parser.add_argument("--session-id", help="Specific session ID")
    parser.add_argument(
        "--lines", type=int, default=200, help="Number of lines to retrieve"
    )
    parser.add_argument("--output", help="Output file for export")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    context = SessionContext(args.session_id)

    if args.command == "recent":
        entries = context.get_recent_context(args.lines)
        if args.json:
            print(json.dumps(entries, indent=2))
        else:
            for entry in entries:
                print(f"[{entry['type']}] {entry.get('content', '')[:100]}")

    elif args.command == "conversation":
        pairs = context.get_conversation_pairs()
        if args.json:
            print(json.dumps(pairs, indent=2))
        else:
            for pair in pairs:
                print(f"User: {pair['user'][:100]}")
                print(f"Assistant: {pair['assistant'][:100]}")
                print("-" * 50)

    elif args.command == "tools":
        usage = context.get_tool_usage()
        if args.json:
            print(json.dumps(usage, indent=2))
        else:
            for tool, uses in usage.items():
                print(f"{tool}: {len(uses)} uses")

    elif args.command == "changes":
        changes = context.get_code_changes()
        if args.json:
            print(json.dumps(changes, indent=2))
        else:
            for change in changes:
                print(f"[{change['tool']}] {change['file']}")

    elif args.command == "errors":
        errors = context.get_errors()
        if args.json:
            print(json.dumps(errors, indent=2))
        else:
            for error in errors:
                print(f"Error: {error['error'][:100]}")
                if error.get("resolution"):
                    print(f"Resolution: {error['resolution'][:100]}")
                print("-" * 50)

    elif args.command == "summary":
        summary = context.get_summary_context()
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            for key, value in summary.items():
                print(f"{key}: {value}")

    elif args.command == "export":
        exported = context.export_context(args.output)
        if args.output:
            print(f"Context exported to {args.output}")
        else:
            print(json.dumps(exported, indent=2))


if __name__ == "__main__":
    main()
