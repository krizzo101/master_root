#!/usr/bin/env python3
"""
Debug script to understand conversation structure
"""

import json
import sys


def debug_conversation(file_path: str):
    """Debug conversation structure"""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    message_data = json.loads(line.strip())

                    msg_type = message_data.get("type", "unknown")
                    timestamp = message_data.get("timestamp", "")

                    if msg_type == "user":
                        content = message_data.get("message", {}).get("content", "")
                        print(f"Line {line_num}: USER - {content[:100]}...")

                    elif msg_type == "assistant":
                        content = message_data.get("message", {}).get("content", "")
                        if isinstance(content, list):
                            text_parts = []
                            for item in content:
                                if (
                                    isinstance(item, dict)
                                    and item.get("type") == "text"
                                ):
                                    text_parts.append(item.get("text", ""))
                            content = " ".join(text_parts)
                        print(f"Line {line_num}: ASSISTANT - {content[:100]}...")

                    if line_num > 10:  # Limit output
                        break

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 debug_conversation.py <chat_log_file>")
        sys.exit(1)

    debug_conversation(sys.argv[1])
