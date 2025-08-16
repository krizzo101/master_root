"""
Text Processing Tools Plugin for MCP Server

This plugin provides text manipulation and analysis tools.
"""

import base64
import hashlib
import re
from typing import Any, Dict, List
from mcp.types import TextContent
import sys
import os

# Add parent directory to path to import BaseTool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_server_template import BaseTool


class TextStatsTool(BaseTool):
    """
    A tool that provides statistics about text content.
    """

    def __init__(self) -> None:
        super().__init__(
            name="text_stats",
            description="Provides statistics about text (word count, character count, etc.)",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to analyze",
                    },
                },
                "required": ["text"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Analyze text and return statistics."""
        self.validate_input(arguments)

        text = arguments["text"]

        # Calculate statistics
        char_count = len(text)
        char_count_no_spaces = len(
            text.replace(" ", "").replace("\n", "").replace("\t", "")
        )
        word_count = len(text.split())
        line_count = text.count("\n") + 1 if text else 0

        # Find most common word
        words = re.findall(r"\b\w+\b", text.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        most_common = (
            max(word_freq.items(), key=lambda x: x[1]) if word_freq else ("", 0)
        )

        stats = f"""Text Statistics:
- Total characters: {char_count}
- Characters (no spaces): {char_count_no_spaces}
- Word count: {word_count}
- Line count: {line_count}
- Most common word: '{most_common[0]}' (appears {most_common[1]} times)"""

        return [TextContent(type="text", text=stats)]


class Base64Tool(BaseTool):
    """
    A tool for Base64 encoding and decoding.
    """

    def __init__(self) -> None:
        super().__init__(
            name="base64",
            description="Encode or decode text using Base64",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["encode", "decode"],
                        "description": "Whether to encode or decode",
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to encode/decode",
                    },
                },
                "required": ["operation", "text"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Perform Base64 encoding or decoding."""
        self.validate_input(arguments)

        operation = arguments["operation"]
        text = arguments["text"]

        try:
            if operation == "encode":
                result = base64.b64encode(text.encode()).decode()
                return [TextContent(type="text", text=f"Encoded: {result}")]
            else:  # decode
                result = base64.b64decode(text).decode()
                return [TextContent(type="text", text=f"Decoded: {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]


class HashTool(BaseTool):
    """
    A tool for generating various hash digests.
    """

    def __init__(self) -> None:
        super().__init__(
            name="hash",
            description="Generate hash digests (MD5, SHA1, SHA256)",
            input_schema={
                "type": "object",
                "properties": {
                    "algorithm": {
                        "type": "string",
                        "enum": ["md5", "sha1", "sha256"],
                        "description": "Hash algorithm to use",
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to hash",
                    },
                },
                "required": ["algorithm", "text"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Generate hash digest."""
        self.validate_input(arguments)

        algorithm = arguments["algorithm"]
        text = arguments["text"]

        text_bytes = text.encode()

        if algorithm == "md5":
            hash_obj = hashlib.md5(text_bytes)
        elif algorithm == "sha1":
            hash_obj = hashlib.sha1(text_bytes)
        else:  # sha256
            hash_obj = hashlib.sha256(text_bytes)

        digest = hash_obj.hexdigest()

        return [
            TextContent(
                type="text",
                text=f"{algorithm.upper()} hash: {digest}",
            )
        ]


class RegexTool(BaseTool):
    """
    A tool for regex pattern matching and replacement.
    """

    def __init__(self) -> None:
        super().__init__(
            name="regex",
            description="Perform regex pattern matching or replacement",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["match", "findall", "replace"],
                        "description": "Regex operation to perform",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern",
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to search in",
                    },
                    "replacement": {
                        "type": "string",
                        "description": "Replacement text (for replace operation)",
                    },
                    "flags": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["IGNORECASE", "MULTILINE", "DOTALL"],
                        },
                        "description": "Regex flags to apply",
                    },
                },
                "required": ["operation", "pattern", "text"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Perform regex operation."""
        self.validate_input(arguments)

        operation = arguments["operation"]
        pattern = arguments["pattern"]
        text = arguments["text"]
        replacement = arguments.get("replacement", "")
        flags_list = arguments.get("flags", [])

        # Build flags
        flags = 0
        for flag_name in flags_list:
            if flag_name == "IGNORECASE":
                flags |= re.IGNORECASE
            elif flag_name == "MULTILINE":
                flags |= re.MULTILINE
            elif flag_name == "DOTALL":
                flags |= re.DOTALL

        try:
            if operation == "match":
                match = re.match(pattern, text, flags)
                if match:
                    result = f"Match found: '{match.group()}' at position {match.start()}-{match.end()}"
                else:
                    result = "No match found"
            elif operation == "findall":
                matches = re.findall(pattern, text, flags)
                if matches:
                    result = f"Found {len(matches)} matches: {matches}"
                else:
                    result = "No matches found"
            else:  # replace
                result_text = re.sub(pattern, replacement, text, flags=flags)
                result = f"Replaced text:\n{result_text}"

            return [TextContent(type="text", text=result)]
        except re.error as e:
            return [TextContent(type="text", text=f"Regex error: {str(e)}")]
