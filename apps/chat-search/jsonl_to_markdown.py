#!/usr/bin/env python3
"""
JSONL to Markdown Converter
Convert chat log JSONL files into readable markdown format
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class JSONLToMarkdownConverter:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else None

    def convert_file(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        include_metadata: bool = True,
        include_tools: bool = True,
        max_response_length: Optional[int] = None,
        filter_content_type: Optional[str] = None,
        compact_mode: bool = False,
        compact_length: int = 1000,
    ) -> str:
        """
        Convert a single JSONL file to markdown

        Args:
            input_file: Path to input JSONL file
            output_file: Path to output markdown file (optional)
            include_metadata: Include message metadata (timestamps, etc.)
            include_tools: Include tool calls and results
            max_response_length: Truncate responses longer than this
            filter_content_type: Only include specific content types ('user', 'assistant', 'tools')

        Returns:
            Path to the generated markdown file
        """
        input_path = Path(input_file)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Generate output filename if not provided
        if output_file is None:
            output_file = input_path.with_suffix(".md")
        else:
            output_file = Path(output_file)

        # Set output directory if specified
        if self.output_dir:
            output_file = self.output_dir / output_file.name

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Read and parse JSONL file
        messages = self._read_jsonl_file(input_path)

        # Filter messages if requested
        if filter_content_type:
            messages = self._filter_messages(messages, filter_content_type)

        # Convert to markdown
        if compact_mode:
            markdown_content = self._convert_to_compact_markdown(
                messages,
                input_path.name,
                include_metadata,
                compact_length,
            )
        else:
            markdown_content = self._convert_to_markdown(
                messages,
                input_path.name,
                include_metadata,
                include_tools,
                max_response_length,
            )

        # Write markdown file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return str(output_file)

    def _read_jsonl_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read and parse JSONL file"""
        messages = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    message_data = json.loads(line)
                    message_data["_line_number"] = line_num
                    messages.append(message_data)
                except json.JSONDecodeError as e:
                    print(
                        f"Warning: Skipping invalid JSON on line {line_num}: {e}",
                        file=sys.stderr,
                    )
                    continue

        return messages

    def _filter_messages(
        self, messages: List[Dict[str, Any]], content_type: str
    ) -> List[Dict[str, Any]]:
        """Filter messages by content type"""
        filtered = []

        for message in messages:
            message_obj = message.get("message", {})
            role = message_obj.get("role", "")

            if content_type == "user" and role == "user":
                filtered.append(message)
            elif content_type == "assistant" and role == "assistant":
                filtered.append(message)
            elif content_type == "tools" and role in ["tool_use", "tool_result"]:
                filtered.append(message)

        return filtered

    def _convert_to_markdown(
        self,
        messages: List[Dict[str, Any]],
        session_name: str,
        include_metadata: bool,
        include_tools: bool,
        max_response_length: Optional[int],
    ) -> str:
        """Convert messages to markdown format"""

        # Header
        markdown = f"# Chat Session: {session_name}\n\n"
        markdown += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown += f"**Total Messages**: {len(messages)}\n\n"

        # Session metadata (from first message if available)
        if messages and include_metadata:
            first_msg = messages[0]
            if "sessionId" in first_msg:
                markdown += f"**Session ID**: `{first_msg['sessionId']}`\n"
            if "cwd" in first_msg:
                markdown += f"**Working Directory**: `{first_msg['cwd']}`\n"
            if "gitBranch" in first_msg:
                markdown += f"**Git Branch**: `{first_msg['gitBranch']}`\n"
            markdown += "\n"

        markdown += "---\n\n"

        # Process messages
        for i, message in enumerate(messages, 1):
            markdown += self._format_message(
                message, i, include_metadata, include_tools, max_response_length
            )
            markdown += "\n\n"

        return markdown

    def _convert_to_compact_markdown(
        self,
        messages: List[Dict[str, Any]],
        session_name: str,
        include_metadata: bool,
        compact_length: int,
    ) -> str:
        """Convert messages to compact markdown format optimized for agent consumption"""

        # Count total interactions first
        total_interactions = 0
        temp_i = 0
        while temp_i < len(messages):
            temp_message = messages[temp_i]
            temp_message_obj = temp_message.get("message", {})
            temp_role = temp_message_obj.get("role", "")
            temp_content = temp_message_obj.get("content", "")

            if temp_role == "user":
                # Check if this is actually a user message (not a tool result)
                is_tool_result = False
                if isinstance(temp_content, list):
                    for item in temp_content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            is_tool_result = True
                            break
                if not is_tool_result:
                    total_interactions += 1
            temp_i += 1

        # Header optimized for agent understanding
        markdown = f"# AGENT BRIEFING: Session Analysis\n"
        markdown += f"**Session ID**: `{messages[0].get('sessionId', 'unknown') if messages else 'unknown'}`\n"
        markdown += (
            f"**Interactions**: {total_interactions} user requests with responses\n"
        )

        # Session context for agent understanding
        if messages and include_metadata:
            first_msg = messages[0]
            if "cwd" in first_msg:
                markdown += f"**Working Directory**: `{first_msg['cwd']}`\n"
            if "gitBranch" in first_msg:
                markdown += f"**Git Branch**: `{first_msg['gitBranch']}`\n"
            timestamp = first_msg.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                    markdown += f"**Session Started**: {formatted_time}\n"
                except Exception:
                    markdown += f"**Session Started**: {timestamp}\n"

        markdown += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown += "\n# CONVERSATION FLOW\n\n"

        # Process messages in compact mode
        interaction_num = 0
        i = 0
        while i < len(messages):
            message = messages[i]
            message_obj = message.get("message", {})
            role = message_obj.get("role", "")
            content = message_obj.get("content", "")

            # Skip tool results and other non-user messages
            if role != "user":
                i += 1
                continue

            # Check if this is actually a user message (not a tool result)
            is_tool_result = False
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        is_tool_result = True
                        break

            if is_tool_result:
                i += 1
                continue

            interaction_num += 1

            # Extract user content
            user_content = ""
            if isinstance(content, str):
                user_content = content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        user_content += item.get("text", "")

            # Look for the next assistant response
            i += 1
            assistant_content = ""
            assistant_tools_used = []

            while i < len(messages):
                next_message = messages[i]
                next_message_obj = next_message.get("message", {})
                next_role = next_message_obj.get("role", "")
                next_content = next_message_obj.get("content", "")

                if next_role == "assistant":
                    # Extract assistant response text
                    if isinstance(next_content, str):
                        assistant_content += next_content
                    elif isinstance(next_content, list):
                        for item in next_content:
                            if isinstance(item, dict):
                                if item.get("type") == "text":
                                    assistant_content += item.get("text", "") + " "
                                elif item.get("type") == "tool_use":
                                    assistant_tools_used.append(
                                        item.get("name", "unknown_tool")
                                    )

                    # If we have content, break and show it
                    if assistant_content.strip():
                        break

                i += 1

            # Compact format - everything on fewer lines
            tools_info = (
                f" [Tools: {', '.join(assistant_tools_used)}]"
                if assistant_tools_used
                else ""
            )

            markdown += (
                f"## {interaction_num}/{total_interactions}. USER: {user_content}\n"
            )

            if assistant_content.strip():
                response_text = (
                    assistant_content[:compact_length].strip() + "..."
                    if len(assistant_content) > compact_length
                    else assistant_content.strip()
                )
                markdown += f"ASSISTANT{tools_info}: {response_text}\n"
            else:
                markdown += f"ASSISTANT{tools_info}: *(No text response found)*\n"

            # Add separator only between interactions
            if interaction_num < total_interactions:
                markdown += "\n"

            i += 1

        # Analyze session for handoff elements
        all_tools_used = set()
        files_accessed = set()
        last_user_request = ""
        session_start = None
        session_end = None
        total_input_tokens = 0
        total_output_tokens = 0
        models_used = set()
        tool_success_count = 0
        tool_failure_count = 0
        interrupted_responses = 0
        cache_hits = 0

        # Extract additional context
        for msg in messages:
            timestamp = msg.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if session_start is None or dt < session_start:
                        session_start = dt
                    if session_end is None or dt > session_end:
                        session_end = dt
                except:
                    pass

            msg_obj = msg.get("message", {})
            content = msg_obj.get("content", "")
            role = msg_obj.get("role", "")

            # Extract performance metrics
            usage = msg_obj.get("usage", {})
            if usage:
                total_input_tokens += usage.get("input_tokens", 0)
                total_output_tokens += usage.get("output_tokens", 0)
                if usage.get("cache_read_input_tokens", 0) > 0:
                    cache_hits += 1

            # Track model usage
            model = msg_obj.get("model", "")
            if model:
                models_used.add(model)

            # Track stop reasons for interruptions
            stop_reason = msg_obj.get("stop_reason")
            if stop_reason and stop_reason != "end_turn":
                interrupted_responses += 1

            # Track last real user request
            if (
                role == "user"
                and isinstance(content, str)
                and not any(
                    isinstance(item, dict) and item.get("type") == "tool_result"
                    for item in (content if isinstance(content, list) else [])
                )
            ):
                last_user_request = (
                    content[:200] + "..." if len(content) > 200 else content
                )

            # Track tool results for success/failure analysis
            tool_use_result = msg.get("toolUseResult")
            if tool_use_result:
                # Simple heuristic: if result contains error indicators, count as failure
                result_str = str(tool_use_result).lower()
                if any(
                    word in result_str
                    for word in ["error", "failed", "exception", "not found"]
                ):
                    tool_failure_count += 1
                else:
                    tool_success_count += 1

            # Extract tools and files
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name", "")
                            all_tools_used.add(tool_name)

                            # Extract file paths from common tools
                            tool_input = item.get("input", {})
                            if "file_path" in tool_input:
                                files_accessed.add(tool_input["file_path"])
                            elif "input" in tool_input and isinstance(
                                tool_input["input"], str
                            ):
                                # Try to find file paths in input strings
                                import re

                                file_matches = re.findall(
                                    r"[/\w\.-]+\.[a-zA-Z]{1,4}", tool_input["input"]
                                )
                                for match in file_matches:
                                    if "/" in match:
                                        files_accessed.add(match)

        # Calculate duration
        duration_str = "Unknown"
        if session_start and session_end:
            duration = session_end - session_start
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            if hours > 0:
                duration_str = f"{hours}h {minutes}m"
            else:
                duration_str = f"{minutes}m"

        # Calculate token efficiency
        total_tools = tool_success_count + tool_failure_count
        tool_success_rate = (
            (tool_success_count / total_tools * 100) if total_tools > 0 else 0
        )

        # Add enhanced summary section
        markdown += f"\n# AGENT HANDOFF ANALYSIS\n"
        markdown += f"**Session Duration**: {duration_str} ({total_interactions} interactions)\n"
        markdown += f"**Last User Request**: {last_user_request}\n"

        # Performance metrics
        if total_input_tokens > 0 or total_output_tokens > 0:
            markdown += f"\n**Performance Metrics**:\n"
            markdown += f"- **Token Usage**: {total_input_tokens:,} input + {total_output_tokens:,} output = {total_input_tokens + total_output_tokens:,} total\n"
            if cache_hits > 0:
                markdown += f"- **Cache Efficiency**: {cache_hits} cache hits\n"
            if interrupted_responses > 0:
                markdown += f"- **Interrupted Responses**: {interrupted_responses}\n"

        # Model tracking
        if models_used:
            markdown += f"**Models Used**: {', '.join(sorted(models_used))}\n"

        # Tool analysis
        if all_tools_used:
            markdown += f"**Tools Used**: {', '.join(sorted(all_tools_used))}\n"
            if total_tools > 0:
                markdown += f"**Tool Success Rate**: {tool_success_rate:.1f}% ({tool_success_count}/{total_tools})\n"

        # File access
        if files_accessed:
            markdown += f"**Files Accessed**: {len(files_accessed)} files\n"
            # Show first few files as examples
            file_list = sorted(files_accessed)[:5]
            for f in file_list:
                markdown += f"  - {f}\n"
            if len(files_accessed) > 5:
                markdown += f"  - ... and {len(files_accessed) - 5} more\n"

        markdown += f"\n**Context for Continuation**:\n"
        markdown += f"- This session contains {total_interactions} user-assistant interactions\n"
        markdown += (
            f"- Tool calls, tool results, and system messages filtered for clarity\n"
        )
        markdown += f"- Each response truncated to {compact_length} characters\n"
        markdown += f"- Review final interactions for current task state\n"

        if interrupted_responses > 0:
            markdown += f"- **Note**: {interrupted_responses} responses were interrupted - check for incomplete tasks\n"

        return markdown

    def _format_message(
        self,
        message: Dict[str, Any],
        message_num: int,
        include_metadata: bool,
        include_tools: bool,
        max_response_length: Optional[int],
    ) -> str:
        """Format a single message as markdown"""

        # Handle different message types
        message_type = message.get("type", "")

        # Skip summary messages
        if message_type == "summary":
            return (
                f"## {message_num}. Session Summary\n\n"
                f"**Summary**: {message.get('summary', 'N/A')}\n\n"
            )

        # Handle regular messages
        message_obj = message.get("message", {})
        role = message_obj.get("role", "unknown")
        content = message_obj.get("content", "")
        timestamp = message.get("timestamp", "")

        # Detect tool result messages (they have "user" role but contain tool_use_id)
        is_tool_result = False
        if role == "user" and isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    is_tool_result = True
                    break

        # Message header
        if is_tool_result:
            header = f"## {message_num}. Tool Result"
        elif role == "user":
            header = f"## {message_num}. User Message"
        elif role == "assistant":
            header = f"## {message_num}. Assistant Response"
        elif role in ["tool_use", "tool_result"]:
            header = f"## {message_num}. Tool {role.replace('_', ' ').title()}"
        else:
            header = f"## {message_num}. {role.title()} Message"

        markdown = f"{header}\n\n"

        # Metadata
        if include_metadata and timestamp:
            try:
                # Parse timestamp and format nicely
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                markdown += f"**Timestamp**: {formatted_time}\n\n"
            except Exception:
                markdown += f"**Timestamp**: {timestamp}\n\n"

        # Content formatting
        if isinstance(content, str):
            formatted_content = self._format_text_content(content, max_response_length)
        elif isinstance(content, list):
            formatted_content = self._format_structured_content(
                content, include_tools, max_response_length
            )
        else:
            formatted_content = str(content)

        markdown += formatted_content

        return markdown

    def _format_text_content(self, content: str, max_length: Optional[int]) -> str:
        """Format plain text content"""
        if max_length and len(content) > max_length:
            content = content[:max_length] + "\n\n*[Content truncated...]*"

        # Escape markdown special characters if needed
        # (Basic escaping - could be enhanced)
        content = content.replace("\\", "\\\\")

        return content

    def _format_structured_content(
        self,
        content: List[Dict[str, Any]],
        include_tools: bool,
        max_length: Optional[int],
    ) -> str:
        """Format structured content (tool calls, etc.)"""
        markdown = ""

        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type", "unknown")

                if item_type == "text":
                    text_content = item.get("text", "")
                    if max_length and len(text_content) > max_length:
                        text_content = (
                            text_content[:max_length] + "\n\n*[Content truncated...]*"
                        )
                    markdown += text_content + "\n\n"

                elif item_type == "tool_use" and include_tools:
                    tool_name = item.get("name", "unknown")
                    tool_input = item.get("input", {})

                    markdown += f"**Tool Used**: `{tool_name}`\n\n"

                    if tool_input:
                        markdown += "**Tool Input**:\n"
                        markdown += "```json\n"
                        markdown += json.dumps(tool_input, indent=2)
                        markdown += "\n```\n\n"

                elif item_type == "tool_result" and include_tools:
                    tool_result = item.get("content", "")
                    is_error = item.get("is_error", False)
                    tool_use_id = item.get("tool_use_id", "")

                    if tool_use_id:
                        markdown += f"**Tool Result** {'(Error)' if is_error else ''} for `{tool_use_id}`:\n"
                    else:
                        markdown += (
                            f"**Tool Result** {'(Error)' if is_error else ''}:\n"
                        )

                    # Try to format as JSON if it looks like JSON
                    if isinstance(tool_result, str) and tool_result.strip().startswith(
                        "{"
                    ):
                        try:
                            parsed = json.loads(tool_result)
                            markdown += "```json\n"
                            markdown += json.dumps(parsed, indent=2)
                            markdown += "\n```\n\n"
                        except Exception:
                            markdown += f"```\n{tool_result}\n```\n\n"
                    else:
                        if max_length and len(str(tool_result)) > max_length:
                            tool_result = (
                                str(tool_result)[:max_length]
                                + "\n\n*[Result truncated...]*"
                            )
                        markdown += f"```\n{tool_result}\n```\n\n"

                else:
                    # Generic structured content
                    markdown += f"**{item_type.title()}**:\n"
                    markdown += "```json\n"
                    markdown += json.dumps(item, indent=2)
                    markdown += "\n```\n\n"

        return markdown

    def convert_directory(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        pattern: str = "*.jsonl",
        **kwargs,
    ) -> List[str]:
        """
        Convert all JSONL files in a directory

        Args:
            input_dir: Directory containing JSONL files
            output_dir: Output directory for markdown files
            pattern: File pattern to match (default: *.jsonl)
            **kwargs: Additional arguments passed to convert_file

        Returns:
            List of generated markdown file paths
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # Find JSONL files
        jsonl_files = list(input_path.glob(pattern))

        if not jsonl_files:
            print(f"No JSONL files found in {input_dir} matching pattern {pattern}")
            return []

        # Convert each file
        generated_files = []
        for jsonl_file in jsonl_files:
            try:
                output_file = self.convert_file(str(jsonl_file), **kwargs)
                generated_files.append(output_file)
                print(f"Converted: {jsonl_file.name} -> {Path(output_file).name}")
            except Exception as e:
                print(f"Error converting {jsonl_file.name}: {e}", file=sys.stderr)

        return generated_files


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSONL chat logs to readable markdown format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file
  python jsonl_to_markdown.py session_123.jsonl

  # Convert with custom output name
  python jsonl_to_markdown.py session_123.jsonl -o session_summary.md

  # Convert all JSONL files in directory
  python jsonl_to_markdown.py -d chat_logs/ -o markdown_output/

  # Convert with options
  python jsonl_to_markdown.py session_123.jsonl --no-metadata --no-tools --max-length 1000

  # Convert only user messages
  python jsonl_to_markdown.py session_123.jsonl --filter user

  # Compact mode - user requests and response previews only
  python jsonl_to_markdown.py session_123.jsonl --compact --compact-length 200
        """,
    )

    parser.add_argument("input", nargs="?", help="Input JSONL file or directory")
    parser.add_argument("-o", "--output", help="Output markdown file or directory")
    parser.add_argument(
        "-d", "--directory", help="Convert all JSONL files in directory"
    )
    parser.add_argument(
        "--pattern",
        default="*.jsonl",
        help="File pattern for directory conversion (default: *.jsonl)",
    )

    # Content options
    parser.add_argument(
        "--no-metadata", action="store_true", help="Exclude message metadata"
    )
    parser.add_argument(
        "--no-tools", action="store_true", help="Exclude tool calls and results"
    )
    parser.add_argument(
        "--max-length", type=int, help="Maximum length for message content"
    )
    parser.add_argument(
        "--filter",
        choices=["user", "assistant", "tools"],
        help="Only include specific content types",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Compact mode: show only user messages and first part of assistant responses",
    )
    parser.add_argument(
        "--compact-length",
        type=int,
        default=1000,
        help="Number of characters to show from assistant responses in compact mode (default: 1000)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.input and not args.directory:
        parser.error("Must specify either input file or directory")

    if args.input and args.directory:
        parser.error("Cannot specify both input file and directory")

    # Create converter
    converter = JSONLToMarkdownConverter()

    try:
        if args.directory:
            # Directory conversion
            generated_files = converter.convert_directory(
                args.directory,
                output_dir=args.output,
                pattern=args.pattern,
                include_metadata=not args.no_metadata,
                include_tools=not args.no_tools,
                max_response_length=args.max_length,
                filter_content_type=args.filter,
            )

            print(f"\nConverted {len(generated_files)} files successfully")

        else:
            # Single file conversion
            output_file = converter.convert_file(
                args.input,
                output_file=args.output,
                include_metadata=not args.no_metadata,
                include_tools=not args.no_tools,
                max_response_length=args.max_length,
                filter_content_type=args.filter,
                compact_mode=args.compact,
                compact_length=args.compact_length,
            )

            print(f"Converted: {args.input} -> {output_file}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
