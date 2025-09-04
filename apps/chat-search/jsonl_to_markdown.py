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
            return (f"## {message_num}. Session Summary\n\n"
                    f"**Summary**: {message.get('summary', 'N/A')}\n\n")

        # Handle regular messages
        message_obj = message.get("message", {})
        role = message_obj.get("role", "unknown")
        content = message_obj.get("content", "")
        timestamp = message.get("timestamp", "")

        # Message header
        if role == "user":
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

                    markdown += f"**Tool Result** {'(Error)' if is_error else ''}:\n"

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
            )

            print(f"Converted: {args.input} -> {output_file}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
