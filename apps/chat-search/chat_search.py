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
from typing import Any, Dict, List


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
            'read': [],
            'write': [],
            'edit': [],
            'delete': [],
            'list': [],
            'other': []
        }
        
        # Map tool names to operation types
        tool_operation_map = {
            'read_file': 'read',
            'read': 'read',
            'Read': 'read',
            'write': 'write',
            'write_file': 'write',
            'Write': 'write',
            'search_replace': 'edit',
            'MultiEdit': 'edit',
            'Edit': 'edit',
            'delete_file': 'delete',
            'Delete': 'delete',
            'list_dir': 'list',
            'glob_file_search': 'list',
            'List': 'list',
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
                                    if isinstance(item, dict) and item.get("type") == "tool_use":
                                        tool_name = item.get("name", "")
                                        tool_input = item.get("input", {})
                                        
                                        # Determine operation type
                                        operation_type = tool_operation_map.get(tool_name, 'other')
                                        
                                        # Extract file path from tool input
                                        file_path_key = None
                                        for key in ['file_path', 'target_file', 'target_directory']:
                                            if key in tool_input:
                                                file_path_key = key
                                                break
                                        
                                        if file_path_key:
                                            file_path_value = tool_input[file_path_key]
                                            file_operations[operation_type].append({
                                                'timestamp': timestamp,
                                                'tool_name': tool_name,
                                                'file_path': file_path_value,
                                                'line': line_num,
                                                'full_input': tool_input if operation_type != 'other' else None
                                            })
                        
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return file_operations
            
        return file_operations

    def extract_conversation_flow(self, file_path: str, response_chars: int = 200) -> List[Dict]:
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
                            user_content = message_data.get("message", {}).get("content", "")
                            timestamp = message_data.get("timestamp", "")
                            
                            # Skip empty, system messages, or tool results
                            if (
                                user_content
                                and isinstance(user_content, str)
                                and not user_content.startswith("<local-command-stdout>")
                                and not user_content.startswith("<command-name>")
                                and not user_content.startswith("Caveat:")
                                and len(user_content.strip()) > 10
                            ):  # Skip very short messages
                                
                                conversation_turns.append({
                                    "turn": len(conversation_turns) + 1,
                                    "type": "user",
                                    "timestamp": timestamp,
                                    "content": user_content,
                                    "line": line_num,
                                })
                        
                        # Extract assistant messages
                        elif message_data.get("type") == "assistant":
                            assistant_content = message_data.get("message", {}).get("content", "")
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
                                    preview_content = full_content[:response_chars] + "..."
                                
                                conversation_turns.append({
                                    "turn": len(conversation_turns) + 1,
                                    "type": "assistant",
                                    "timestamp": timestamp,
                                    "content": preview_content,
                                    "full_length": len(full_content),
                                    "line": line_num,
                                })
                        
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return []
        
        return conversation_turns


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
