#!/usr/bin/env python3
"""
Conversation Flow Extractor
Extracts user prompts and agent responses for session handoff review
"""

import json
import sys
from typing import Dict, List, Tuple


def extract_conversation_flow(file_path: str, response_chars: int = 200) -> List[Dict]:
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
                            and not user_content.startswith("<local-command-stdout>")
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
                                # Extract text content from structured messages
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


def print_conversation_flow(
    conversation_turns: List[Dict], show_timestamps: bool = True
):
    """Print conversation flow in a readable format"""

    if not conversation_turns:
        print("No conversation found.")
        return

    print("Conversation Flow Summary:")
    print("=" * 60)

    for turn in conversation_turns:
        timestamp = ""
        if show_timestamps and turn["timestamp"]:
            # Format timestamp
            if "T" in turn["timestamp"]:
                timestamp = turn["timestamp"].split("T")[1][:8] + " | "
            else:
                timestamp = turn["timestamp"][:8] + " | "

        if turn["type"] == "user":
            print(f"\n{turn['turn']}. USER PROMPT:")
            print(f"   {timestamp}{turn['content']}")
        else:
            response_info = ""
            if "full_length" in turn and turn["full_length"] > 200:
                response_info = f" ({turn['full_length']} chars total)"

            print(f"\n{turn['turn']}. AGENT RESPONSE{response_info}:")
            print(f"   {timestamp}{turn['content']}")


def print_conversation_stats(conversation_turns: List[Dict]):
    """Print conversation statistics"""

    user_turns = [t for t in conversation_turns if t["type"] == "user"]
    assistant_turns = [t for t in conversation_turns if t["type"] == "assistant"]

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


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 conversation_flow_extractor.py <chat_log_file> [options]")
        print("Options:")
        print(
            "  --response-chars N    Number of characters to show from responses (default: 200)"
        )
        print("  --no-timestamps       Hide timestamps")
        print("  --stats-only          Show only conversation statistics")
        print(
            "Example: python3 conversation_flow_extractor.py chat_logs/0678c5b6-69e0-41bb-9232-61b098314ad6.jsonl"
        )
        sys.exit(1)

    file_path = sys.argv[1]
    response_chars = 200
    show_timestamps = True
    stats_only = False

    # Parse options
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--response-chars" and i + 1 < len(sys.argv):
            response_chars = int(sys.argv[i + 1])
        elif arg == "--no-timestamps":
            show_timestamps = False
        elif arg == "--stats-only":
            stats_only = True

    print(f"Analyzing conversation flow: {file_path}")
    print("=" * 60)

    conversation_turns = extract_conversation_flow(file_path, response_chars)

    if stats_only:
        print_conversation_stats(conversation_turns)
    else:
        print_conversation_flow(conversation_turns, show_timestamps)
        print_conversation_stats(conversation_turns)


if __name__ == "__main__":
    main()
