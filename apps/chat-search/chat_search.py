#!/usr/bin/env python3
"""
Fast Chat Log Search Utility
Quickly search through chat_logs/*.jsonl files
"""

import argparse
import glob
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class ChatSearcher:
    def __init__(self, log_dir="chat_logs"):
        self.log_dir = log_dir

    def search(
        self,
        query: str,
        content_type: str = "all",
        limit: int = 10,
        context: bool = True,
        date_from: str = None,
        date_to: str = None,
        files_filter: List[str] = None,
    ) -> List[Dict]:
        """
        Search through chat logs

        Args:
            query: Search term (regex supported)
            content_type: 'user', 'assistant', 'all', 'tools'
            limit: Max results to return
            context: Include surrounding context
            date_from: Start date filter (YYYY-MM-DD format)
            date_to: End date filter (YYYY-MM-DD format)
            files_filter: List of specific files to search (exact filenames)
        """
        results = []
        pattern = re.compile(query, re.IGNORECASE)

        # Get all JSONL files and group messages by session for context
        jsonl_files = glob.glob(f"{self.log_dir}/*.jsonl")

        # Filter by specific files if requested
        if files_filter:
            jsonl_files = [
                f for f in jsonl_files if any(fname in f for fname in files_filter)
            ]

        sessions = defaultdict(list)

        # First pass: group messages by session
        for file_path in jsonl_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            message_data = json.loads(line.strip())
                            session_id = message_data.get("sessionId", "unknown")
                            sessions[session_id].append(
                                {
                                    "data": message_data,
                                    "file": file_path,
                                    "line": line_num,
                                }
                            )
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Error reading {file_path}: {e}", file=sys.stderr)
                continue

        # Second pass: search within sessions
        for session_id, messages in sessions.items():
            # Sort messages by timestamp
            messages.sort(key=lambda x: x["data"].get("timestamp", ""))

            for i, msg_info in enumerate(messages):
                message_data = msg_info["data"]
                match = self._search_message_data(message_data, pattern, content_type)

                if match:
                    # Check date filters if specified
                    timestamp_str = message_data.get("timestamp", "")
                    if date_from or date_to:
                        try:
                            # Extract date from timestamp (assuming ISO format)
                            msg_date = (
                                timestamp_str.split("T")[0]
                                if "T" in timestamp_str
                                else timestamp_str[:10]
                            )
                            if date_from and msg_date < date_from:
                                continue
                            if date_to and msg_date > date_to:
                                continue
                        except (ValueError, IndexError):
                            # Skip if timestamp parsing fails
                            continue

                    # Build context from surrounding messages
                    context_info = {}
                    if context:
                        if i > 0:
                            prev_msg = messages[i - 1]["data"].get("message", {})
                            context_info["prev_message"] = prev_msg.get("content", "")[
                                :200
                            ]
                            context_info["prev_role"] = prev_msg.get("role", "")
                        if i < len(messages) - 1:
                            next_msg = messages[i + 1]["data"].get("message", {})
                            context_info["next_message"] = next_msg.get("content", "")[
                                :200
                            ]
                            context_info["next_role"] = next_msg.get("role", "")
                        context_info["session_id"] = session_id
                        context_info["message_index"] = i
                        context_info["total_messages"] = len(messages)

                    result = {
                        "file": msg_info["file"],
                        "line": msg_info["line"],
                        "timestamp": message_data.get("timestamp", "unknown"),
                        "session_id": session_id,
                        "match_type": match["type"],
                        "content": match["content"][:500]
                        + ("..." if len(match["content"]) > 500 else ""),
                        "full_content": match["content"],
                        "context": context_info if context else {},
                    }
                    results.append(result)

                    if len(results) >= limit:
                        return results

        return results

    def _search_message_data(
        self, message_data: Dict, pattern: re.Pattern, content_type: str
    ) -> Dict:
        """Search within a single message"""
        message = message_data.get("message", {})
        role = message.get("role", "")
        content = message.get("content", "")

        # Check if we should search this message type
        if content_type == "user" and role != "user":
            return None
        elif content_type == "assistant" and role != "assistant":
            return None
        elif content_type == "tools" and role not in ["tool_use", "tool_result"]:
            return None

        # Handle different content types
        if isinstance(content, str):
            if pattern.search(content):
                return {"type": f"{role}_message", "content": content}
        elif isinstance(content, list):
            # Handle structured content (tool calls, etc.)
            for item in content:
                if isinstance(item, dict):
                    text_content = json.dumps(item, indent=2)
                    if pattern.search(text_content):
                        return {"type": f"{role}_structured", "content": text_content}

        return None

    def list_files(self) -> List[str]:
        """List available chat log files with basic info"""
        files = []
        jsonl_files = glob.glob(f"{self.log_dir}/*.jsonl")

        for file_path in sorted(jsonl_files):
            try:
                with open(file_path, "r") as f:
                    line_count = sum(1 for _ in f)

                # Get first line for timestamp
                with open(file_path, "r") as f:
                    first_line = f.readline().strip()
                    if first_line:
                        try:
                            first_chat = json.loads(first_line)
                            timestamp = first_chat.get("create_time", "unknown")
                        except:
                            timestamp = "unknown"
                    else:
                        timestamp = "unknown"

                files.append(
                    {
                        "file": file_path,
                        "sessions": line_count,
                        "first_timestamp": timestamp,
                    }
                )
            except Exception as e:
                files.append(
                    {
                        "file": file_path,
                        "sessions": "error",
                        "first_timestamp": f"error: {e}",
                    }
                )

        return files

    def extract_files_used(self, file_path: str) -> Dict[str, List[Dict]]:
        """
        Extract all file operations from a chat log file

        Args:
            file_path: Path to the JSONL chat log file

        Returns:
            Dictionary with file operations categorized by type
        """
        file_operations = {
            "read": [],
            "write": [],
            "edit": [],
            "delete": [],
            "list": [],
            "other": [],
        }

        # Map tool names to operation types
        tool_operation_map = {
            "read_file": "read",
            "read": "read",
            "Read": "read",
            "write": "write",
            "write_file": "write",
            "Write": "write",
            "search_replace": "edit",
            "MultiEdit": "edit",
            "Edit": "edit",
            "delete_file": "delete",
            "Delete": "delete",
            "list_dir": "list",
            "glob_file_search": "list",
            "List": "list",
        }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        message_data = json.loads(line.strip())

                        # Look for assistant tool calls
                        if message_data.get("type") == "assistant":
                            content = message_data.get("message", {}).get("content", "")
                            timestamp = message_data.get("timestamp", "")

                            if isinstance(content, list):
                                for item in content:
                                    if (
                                        isinstance(item, dict)
                                        and item.get("type") == "tool_use"
                                    ):
                                        tool_name = item.get("name", "")
                                        tool_input = item.get("input", {})

                                        # Determine operation type
                                        operation_type = tool_operation_map.get(
                                            tool_name, "other"
                                        )

                                        # Extract file path from tool input
                                        file_path_key = None
                                        for key in [
                                            "file_path",
                                            "target_file",
                                            "target_directory",
                                        ]:
                                            if key in tool_input:
                                                file_path_key = key
                                                break

                                        if file_path_key:
                                            file_path_value = tool_input[file_path_key]
                                            file_operations[operation_type].append(
                                                {
                                                    "timestamp": timestamp,
                                                    "tool_name": tool_name,
                                                    "file_path": file_path_value,
                                                    "line": line_num,
                                                    "full_input": (
                                                        tool_input
                                                        if operation_type != "other"
                                                        else None
                                                    ),
                                                }
                                            )

                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        continue

        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return file_operations

        return file_operations

    def extract_conversation_flow(
        self, file_path: str, response_chars: int = 200
    ) -> List[Dict]:
        """
        Extract user prompts and agent responses from a chat session

        Args:
            file_path: Path to the JSONL chat log file
            response_chars: Number of characters to show from agent responses

        Returns:
            List of conversation turns with user prompts and agent response previews
        """
        conversation_turns = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        message_data = json.loads(line.strip())

                        # Extract user messages
                        if message_data.get("type") == "user":
                            user_content = message_data.get("message", {}).get(
                                "content", ""
                            )
                            timestamp = message_data.get("timestamp", "")

                            # Skip empty, system messages, or tool results
                            if (
                                user_content
                                and isinstance(user_content, str)
                                and not user_content.startswith(
                                    "<local-command-stdout>"
                                )
                                and not user_content.startswith("<command-name>")
                                and not user_content.startswith("Caveat:")
                                and len(user_content.strip()) > 10
                            ):  # Skip very short messages
                                conversation_turns.append(
                                    {
                                        "turn": len(conversation_turns) + 1,
                                        "type": "user",
                                        "timestamp": timestamp,
                                        "content": user_content,
                                        "line": line_num,
                                    }
                                )

                        # Extract assistant messages
                        elif message_data.get("type") == "assistant":
                            assistant_content = message_data.get("message", {}).get(
                                "content", ""
                            )
                            timestamp = message_data.get("timestamp", "")

                            if assistant_content:
                                # Handle both string and array content
                                if isinstance(assistant_content, list):
                                    text_parts = []
                                    for item in assistant_content:
                                        if isinstance(item, dict):
                                            if item.get("type") == "text":
                                                text_parts.append(item.get("text", ""))
                                            elif item.get("type") == "tool_use":
                                                tool_name = item.get("name", "unknown")
                                                text_parts.append(f"[Used {tool_name}]")

                                    full_content = " ".join(text_parts)
                                else:
                                    full_content = assistant_content

                                # Truncate response if too long
                                preview_content = full_content
                                if len(full_content) > response_chars:
                                    preview_content = (
                                        full_content[:response_chars] + "..."
                                    )

                                conversation_turns.append(
                                    {
                                        "turn": len(conversation_turns) + 1,
                                        "type": "assistant",
                                        "timestamp": timestamp,
                                        "content": preview_content,
                                        "full_length": len(full_content),
                                        "line": line_num,
                                    }
                                )

                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        continue

        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return []

        return conversation_turns

    def extract_tools_used(self, file_path: str) -> Dict[str, Dict]:
        """
        Extract all tool calls from a chat log file

        Args:
            file_path: Path to the JSONL chat log file

        Returns:
            Dictionary with tool usage statistics
        """
        tool_usage = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        message_data = json.loads(line.strip())

                        # Look for assistant tool calls
                        if message_data.get("type") == "assistant":
                            content = message_data.get("message", {}).get("content", "")
                            timestamp = message_data.get("timestamp", "")

                            if isinstance(content, list):
                                for item in content:
                                    if (
                                        isinstance(item, dict)
                                        and item.get("type") == "tool_use"
                                    ):
                                        tool_name = item.get("name", "")

                                        if tool_name:
                                            if tool_name not in tool_usage:
                                                tool_usage[tool_name] = {
                                                    "count": 0,
                                                    "first_used": timestamp,
                                                    "last_used": timestamp,
                                                    "line_numbers": [],
                                                }

                                            tool_usage[tool_name]["count"] += 1
                                            tool_usage[tool_name][
                                                "last_used"
                                            ] = timestamp
                                            tool_usage[tool_name][
                                                "line_numbers"
                                            ].append(line_num)

                                            # Set first_used if this is the first occurrence
                                            if tool_usage[tool_name]["count"] == 1:
                                                tool_usage[tool_name][
                                                    "first_used"
                                                ] = timestamp

                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        continue

        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return {}

        return tool_usage

    def extract_handoff_summary(
        self, file_path: str, response_chars: int = 150
    ) -> Dict:
        """
        Extract comprehensive handoff summary from a chat log file

        Args:
            file_path: Path to the JSONL chat log file
            response_chars: Number of characters to show from agent responses

        Returns:
            Dictionary with complete handoff information
        """
        # Get all the data we need
        conversation_turns = self.extract_conversation_flow(file_path, response_chars)
        file_ops = self.extract_files_used(file_path)
        tool_usage = self.extract_tools_used(file_path)

        # Extract user prompts and agent responses
        user_prompts = [t for t in conversation_turns if t["type"] == "user"]
        agent_responses = [t for t in conversation_turns if t["type"] == "assistant"]

        # Get session timing
        first_timestamp = None
        last_timestamp = None
        if conversation_turns:
            first_timestamp = conversation_turns[0]["timestamp"]
            last_timestamp = conversation_turns[-1]["timestamp"]

        # Determine session purpose from first user prompt
        session_purpose = "Unknown"
        if user_prompts:
            first_prompt = user_prompts[0]["content"]
            # Extract first 100 chars as purpose
            session_purpose = (
                first_prompt[:100] + "..." if len(first_prompt) > 100 else first_prompt
            )

        # Count file operations
        file_summary = {}
        for op_type, operations in file_ops.items():
            if operations:
                file_summary[op_type.upper()] = len(operations)

        # Count tool usage
        tool_summary = {}
        total_tool_calls = 0
        for tool_name, usage in tool_usage.items():
            tool_summary[tool_name] = usage["count"]
            total_tool_calls += usage["count"]

        return {
            "file_path": file_path,
            "session_stats": {
                "total_turns": len(conversation_turns),
                "user_prompts": len(user_prompts),
                "agent_responses": len(agent_responses),
                "first_timestamp": first_timestamp,
                "last_timestamp": last_timestamp,
            },
            "session_purpose": session_purpose,
            "user_prompts": user_prompts,
            "agent_responses": agent_responses,
            "file_operations": file_summary,
            "tool_usage": tool_summary,
            "total_tool_calls": total_tool_calls,
            "unique_tools": len(tool_usage),
        }


def main():
    parser = argparse.ArgumentParser(description="Search chat logs quickly")
    parser.add_argument("query", nargs="?", help="Search query (regex supported)")
    parser.add_argument(
        "--type",
        "-t",
        choices=["user", "assistant", "all", "tools"],
        default="all",
        help="Content type to search",
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Maximum results to return"
    )
    parser.add_argument(
        "--no-context", action="store_true", help="Disable context output"
    )
    parser.add_argument(
        "--files", "-f", action="store_true", help="List available chat log files"
    )
    parser.add_argument("--dir", "-d", default="chat_logs", help="Chat logs directory")
    parser.add_argument("--date-from", help="Start date filter (YYYY-MM-DD)")
    parser.add_argument("--date-to", help="End date filter (YYYY-MM-DD)")
    parser.add_argument(
        "--file-filter", nargs="+", help="Search only these specific files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full verbose output (default is concise)",
    )
    parser.add_argument(
        "--list-files-used",
        action="store_true",
        help="Extract and list all files referenced in the session",
    )
    parser.add_argument(
        "--conversation-flow",
        action="store_true",
        help="Extract conversation flow (user prompts + agent response previews)",
    )
    parser.add_argument(
        "--response-chars",
        type=int,
        default=200,
        help="Number of characters to show from agent responses (default: 200)",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Show only conversation statistics (use with --conversation-flow)",
    )
    parser.add_argument(
        "--list-tools-used",
        action="store_true",
        help="Extract and list all tools used in the session",
    )
    parser.add_argument(
        "--handoff",
        action="store_true",
        help="Generate comprehensive handoff summary (combines all analysis features)",
    )

    args = parser.parse_args()

    searcher = ChatSearcher(args.dir)

    if args.files:
        print("Available chat log files:")
        files = searcher.list_files()
        for file_info in files:
            print(
                f"  {file_info['file']} - {file_info['sessions']} sessions - {file_info['first_timestamp']}"
            )
        return

    # Handle file extraction mode
    if args.list_files_used:
        if not args.file_filter or len(args.file_filter) != 1:
            print(
                "Error: --list-files-used requires exactly one file specified with --file-filter"
            )
            print(
                "Example: python3 chat_search.py --list-files-used --file-filter 0678c5b6-69e0-41bb-9232-61b098314ad6.jsonl"
            )
            return

        file_path = f"{args.dir}/{args.file_filter[0]}"
        print(f"Extracting file operations from: {file_path}")
        print("=" * 60)

        file_ops = searcher.extract_files_used(file_path)

        # Print file operations by category
        for op_type, operations in file_ops.items():
            if operations:
                print(f"\n{op_type.upper()} OPERATIONS ({len(operations)} files):")
                for op in operations:
                    timestamp = op["timestamp"][:19] if op["timestamp"] else "unknown"
                    if args.verbose and op["full_input"]:
                        print(f"  {timestamp} | {op['tool_name']} | {op['file_path']}")
                        print(f"    Input: {op['full_input']}")
                    else:
                        print(f"  {timestamp} | {op['tool_name']} | {op['file_path']}")

        # Summary
        total_ops = sum(len(ops) for ops in file_ops.values())
        print(f"\nSUMMARY: {total_ops} total file operations")
        return

    # Handle conversation flow extraction mode
    if args.conversation_flow:
        if not args.file_filter or len(args.file_filter) != 1:
            print(
                "Error: --conversation-flow requires exactly one file specified with --file-filter"
            )
            print(
                "Example: python3 chat_search.py --conversation-flow --file-filter 0678c5b6-69e0-41bb-9232-61b098314ad6.jsonl"
            )
            return

        file_path = f"{args.dir}/{args.file_filter[0]}"
        print(f"Analyzing conversation flow: {file_path}")
        print("=" * 60)

        conversation_turns = searcher.extract_conversation_flow(
            file_path, args.response_chars
        )

        if args.stats_only:
            # Print only statistics
            user_turns = [t for t in conversation_turns if t["type"] == "user"]
            assistant_turns = [
                t for t in conversation_turns if t["type"] == "assistant"
            ]

            print(f"Conversation Statistics:")
            print(f"  Total turns: {len(conversation_turns)}")
            print(f"  User prompts: {len(user_turns)}")
            print(f"  Agent responses: {len(assistant_turns)}")

            if assistant_turns:
                total_chars = sum(
                    t.get("full_length", len(t["content"])) for t in assistant_turns
                )
                avg_chars = total_chars // len(assistant_turns)
                print(f"  Average response length: {avg_chars} characters")
                print(f"  Total agent output: {total_chars} characters")
        else:
            # Print full conversation flow
            if not conversation_turns:
                print("No conversation found.")
                return

            print("Conversation Flow Summary:")
            print("=" * 60)

            for turn in conversation_turns:
                timestamp = ""
                if turn["timestamp"] and not args.no_context:
                    if "T" in turn["timestamp"]:
                        timestamp = turn["timestamp"][:8] + " | "
                    else:
                        timestamp = turn["timestamp"][:8] + " | "

                if turn["type"] == "user":
                    print(f"\n{turn['turn']}. USER PROMPT:")
                    print(f"   {timestamp}{turn['content']}")
                else:
                    response_info = ""
                    if (
                        "full_length" in turn
                        and turn["full_length"] > args.response_chars
                    ):
                        response_info = f" ({turn['full_length']} chars total)"

                    print(f"\n{turn['turn']}. AGENT RESPONSE{response_info}:")
                    print(f"   {timestamp}{turn['content']}")

            # Print statistics at the end
            user_turns = [t for t in conversation_turns if t["type"] == "user"]
            assistant_turns = [
                t for t in conversation_turns if t["type"] == "assistant"
            ]

            print(f"\nConversation Statistics:")
            print(f"  Total turns: {len(conversation_turns)}")
            print(f"  User prompts: {len(user_turns)}")
            print(f"  Agent responses: {len(assistant_turns)}")

            if assistant_turns:
                total_chars = sum(
                    t.get("full_length", len(t["content"])) for t in assistant_turns
                )
                avg_chars = total_chars // len(assistant_turns)
                print(f"  Average response length: {avg_chars} characters")
                print(f"  Total agent output: {total_chars} characters")

        return

    # Handle tool usage extraction mode
    if args.list_tools_used:
        if not args.file_filter or len(args.file_filter) != 1:
            print(
                "Error: --list-tools-used requires exactly one file specified with --file-filter"
            )
            print(
                "Example: python3 chat_search.py --list-tools-used --file-filter 0678c5b6-69e0-41bb-9232-61b098314ad6.jsonl"
            )
            return

        file_path = f"{args.dir}/{args.file_filter[0]}"
        print(f"Extracting tool usage from: {file_path}")
        print("=" * 60)

        tool_usage = searcher.extract_tools_used(file_path)

        if not tool_usage:
            print("No tool usage found.")
            return

        print("TOOL USAGE SUMMARY:")
        total_calls = 0
        for tool_name, usage in sorted(
            tool_usage.items(), key=lambda x: x[1]["count"], reverse=True
        ):
            first_time = usage["first_used"][:8] if usage["first_used"] else "unknown"
            last_time = usage["last_used"][:8] if usage["last_used"] else "unknown"
            print(
                f"  {tool_name}: {usage['count']} calls (first: {first_time}, last: {last_time})"
            )
            total_calls += usage["count"]

        print(
            f"\nTOTAL: {total_calls} tool calls across {len(tool_usage)} unique tools"
        )
        return

    # Handle comprehensive handoff mode
    if args.handoff:
        if not args.file_filter or len(args.file_filter) != 1:
            print(
                "Error: --handoff requires exactly one file specified with --file-filter"
            )
            print(
                "Example: python3 chat_search.py --handoff --file-filter 0678c5b6-69e0-41bb-9232-61b098314ad6.jsonl"
            )
            return

        file_path = f"{args.dir}/{args.file_filter[0]}"
        print(f"Generating handoff summary for: {file_path}")
        print("=" * 80)

        handoff_data = searcher.extract_handoff_summary(file_path, args.response_chars)

        # Session overview
        stats = handoff_data["session_stats"]
        print(f"=== SESSION HANDOFF SUMMARY ===")
        print(f"File: {handoff_data['file_path']}")
        print(
            f"Session: {stats['total_turns']} turns ({stats['user_prompts']} user prompts, {stats['agent_responses']} agent responses)"
        )

        if stats["first_timestamp"] and stats["last_timestamp"]:
            first_time = (
                stats["first_timestamp"][:19] if stats["first_timestamp"] else "unknown"
            )
            last_time = (
                stats["last_timestamp"][:19] if stats["last_timestamp"] else "unknown"
            )
            print(f"Duration: {first_time} → {last_time}")

        print(f"Purpose: {handoff_data['session_purpose']}")
        print()

        # User requests
        print("=== USER REQUESTS ===")
        for i, prompt in enumerate(handoff_data["user_prompts"], 1):
            content = (
                prompt["content"][:200] + "..."
                if len(prompt["content"]) > 200
                else prompt["content"]
            )
            print(f"{i}. {content}")
        print()

        # Agent accomplishments (first few responses)
        print("=== AGENT ACCOMPLISHMENTS ===")
        for i, response in enumerate(handoff_data["agent_responses"][:5], 1):
            content = (
                response["content"][:150] + "..."
                if len(response["content"]) > 150
                else response["content"]
            )
            print(f"{i}. {content}")

        if len(handoff_data["agent_responses"]) > 5:
            print(f"... and {len(handoff_data['agent_responses']) - 5} more responses")
        print()

        # Files modified
        print("=== FILES MODIFIED ===")
        for op_type, count in handoff_data["file_operations"].items():
            print(f"{op_type}: {count} files")
        print()

        # Tools used
        print("=== TOOLS USED ===")
        tool_summary = handoff_data["tool_usage"]
        tool_list = []
        for tool_name, count in sorted(
            tool_summary.items(), key=lambda x: x[1], reverse=True
        ):
            tool_list.append(f"{tool_name}: {count} calls")
        print(" | ".join(tool_list))
        print()

        # Summary
        print("=== SESSION SUMMARY ===")
        print(f"Total tool calls: {handoff_data['total_tool_calls']}")
        print(f"Unique tools used: {handoff_data['unique_tools']}")
        print(f"Files touched: {sum(handoff_data['file_operations'].values())}")
        print()

        # Next steps assessment
        print("=== NEXT STEPS ===")
        if handoff_data["user_prompts"] and handoff_data["agent_responses"]:
            last_user_prompt = handoff_data["user_prompts"][-1]
            last_agent_response = handoff_data["agent_responses"][-1]

            # Simple heuristic: if last response is much longer, likely completed
            if len(last_agent_response["content"]) > 200:
                print("Previous agent appears to have completed the requested tasks.")
            else:
                print(
                    "Previous agent may have been in progress. Review last responses for context."
                )
        else:
            print("Unable to determine session completion status.")

        return

    if not args.query:
        parser.print_help()
        return

    results = searcher.search(
        query=args.query,
        content_type=args.type,
        limit=args.limit,
        context=not args.no_context,
        date_from=args.date_from,
        date_to=args.date_to,
        files_filter=args.file_filter,
    )

    if not results:
        print(f"No matches found for: {args.query}")
        return

    if args.verbose:
        # Original verbose output
        print(f"Found {len(results)} matches for: {args.query}\n")

        for i, result in enumerate(results, 1):
            print(f"=== Result {i} ===")
            print(f"File: {result['file']}")
            print(f"Time: {result['timestamp']}")
            print(f"Type: {result['match_type']}")
            print(f"Content: {result['content']}")

            if result["context"] and not args.no_context:
                ctx = result["context"]
                if "prev_message" in ctx and ctx["prev_message"]:
                    print(f"Previous: {ctx['prev_message']}")
                if "next_message" in ctx and ctx["next_message"]:
                    print(f"Next: {ctx['next_message']}")

            print()
    else:
        # Concise output for agent handoffs (default)
        print(f"Found {len(results)} matches for: {args.query}\n")
        for i, result in enumerate(results, 1):
            # Extract key info only
            timestamp = (
                result["timestamp"].split("T")[0]
                + " "
                + result["timestamp"].split("T")[1][:8]
                if "T" in result["timestamp"]
                else result["timestamp"]
            )
            msg_type = (
                result["match_type"].replace("_message", "").replace("_structured", "")
            )

            # Summarize content intelligently
            content = result["content"]

            # Check if content looks like JSON (starts with { and contains tool info)
            if content.strip().startswith("{") and (
                '"name":' in content or '"tool_use_id":' in content
            ):
                try:
                    import re

                    # Extract tool name from JSON
                    tool_name_match = re.search(r'"name":\s*"([^"]+)"', content)
                    if tool_name_match:
                        tool_name = tool_name_match.group(1)
                        summary = f"Used {tool_name}"
                        # Try to extract first parameter
                        input_match = re.search(r'"input":\s*{[^}]*"([^"]+)":', content)
                        if input_match:
                            summary += f" ({input_match.group(1)}=...)"
                    else:
                        # Check for tool result
                        if '"tool_result"' in content or '"tool_use_id"' in content:
                            if (
                                "error" in content.lower()
                                or "failed" in content.lower()
                            ):
                                summary = "Tool failed"
                            elif (
                                "success" in content.lower()
                                or "completed" in content.lower()
                            ):
                                summary = "Tool succeeded"
                            else:
                                summary = "Tool result"
                        else:
                            # Generic JSON - just show type or first few words
                            type_match = re.search(r'"type":\s*"([^"]+)"', content)
                            if type_match:
                                summary = f"Content: {type_match.group(1)}"
                            else:
                                summary = (
                                    content[:60].replace("\n", " ").strip() + "..."
                                )
                except:
                    summary = content[:60].replace("\n", " ").strip() + "..."
            else:
                # Plain text content - truncate appropriately
                if "user" in result["match_type"]:
                    summary = content[:100].replace("\n", " ").strip()
                    if len(content) > 100:
                        summary += "..."
                else:
                    summary = content[:80].replace("\n", " ").strip()
                    if len(content) > 80:
                        summary += "..."

            print(f"{timestamp} | {msg_type} | {summary}")


if __name__ == "__main__":
    main()
