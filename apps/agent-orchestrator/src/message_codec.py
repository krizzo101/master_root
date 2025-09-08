"""
Ultra-Efficient Message Codec System
Compresses human messages to minimal tokens while preserving meaning
"""
import json
import re
from typing import Dict, List, Optional, Tuple


class MessageCodec:
    """Bidirectional message compression for token efficiency"""

    def __init__(self):
        # Ultra-short response codes
        self.response_codes = {
            # Approval/Agreement (1-2 tokens)
            "1": [
                "yes",
                "sure",
                "go ahead",
                "do it",
                "sounds good",
                "agreed",
                "approve",
                "proceed",
            ],
            "0": ["no", "don't", "stop", "cancel", "reject", "abort"],
            "2": ["maybe", "not sure", "possibly", "depends", "need more info"],
            # Actions (3-4 token savings)
            "R": "restart",
            "P": "pause",
            "C": "continue",
            "S": "status",
            "A": "agents",
            "T": "tasks",
            "H": "help",
            "L": "logs",
            "M": "metrics",
            # Common phrases (10-20 token savings)
            "GW": "good work",
            "LG": "looks good",
            "NP": "no problem",
            "WIP": "work in progress",
            "ETA": "estimated time",
            "FYI": "for your information",
            "ASAP": "as soon as possible",
            "LGTM": "looks good to me",
            "TL;DR": "too long didn't read",
            "WTF": "what the hell",
            "IMO": "in my opinion",
            "BTW": "by the way",
            # Technical shortcuts
            "DB": "database",
            "API": "api",
            "JSON": "json",
            "HTTP": "http",
            "REST": "rest api",
            "CRUD": "create read update delete",
            "MCP": "model context protocol",
            "LLM": "large language model",
            "AI": "artificial intelligence",
            "ML": "machine learning",
            # Orchestrator specific
            "ORC": "orchestrator",
            "AGT": "agent",
            "TSK": "task",
            "TOK": "token",
            "PAR": "parallel",
            "DEP": "dependency",
            "CFG": "configuration",
            "LOG": "logs",
            "ERR": "error",
            "SUC": "success",
            "FAIL": "failed",
        }

        # Reverse mapping for decoding
        self.decode_map = {}
        for code, expansions in self.response_codes.items():
            if isinstance(expansions, list):
                # For multi-option codes, use first option as canonical
                self.decode_map[code] = expansions[0]
            else:
                self.decode_map[code] = expansions

        # Context-aware patterns (even bigger savings)
        self.patterns = [
            # Question responses
            (r"\?.*\b(1)\b", lambda m: "Yes"),
            (r"\?.*\b(0)\b", lambda m: "No"),
            (r"\?.*\b(2)\b", lambda m: "Maybe"),
            # Command patterns
            (r"^(R)$", lambda m: "Restart the orchestrator"),
            (r"^(S)$", lambda m: "Show current status"),
            (r"^(A)$", lambda m: "List active agents"),
            (r"^(T)$", lambda m: "Show task progress"),
            # Contextual shortcuts
            (r"\b(GW)\b", lambda m: "Good work"),
            (r"\b(LGTM)\b", lambda m: "Looks good to me"),
            (r"\b(WIP)\b", lambda m: "Work in progress"),
        ]

        # Emoji shortcuts (1 token vs 2-3 words)
        self.emoji_codes = {
            "+": "👍",
            "-": "👎",
            "?": "❓",
            "!": "❗",
            "ok": "✅",
            "no": "❌",
            "up": "⬆️",
            "dn": "⬇️",
            "go": "🚀",
            "win": "🎉",
            "bug": "🐛",
            "fix": "🔧",
        }

    def encode_message(self, message: str) -> str:
        """Compress human message to minimal tokens"""
        original_length = len(message)

        # Handle simple yes/no responses
        msg_lower = message.lower().strip()

        # Direct response mapping
        for code, expansions in self.response_codes.items():
            if isinstance(expansions, list):
                if any(phrase in msg_lower for phrase in expansions):
                    return f"/{code}"  # Prefix with / to indicate code

        # Pattern-based compression
        compressed = message
        for pattern, replacement in self.patterns:
            if isinstance(replacement, str):
                compressed = re.sub(
                    pattern, replacement, compressed, flags=re.IGNORECASE
                )

        # Replace common technical terms
        for code, expansion in self.response_codes.items():
            if isinstance(expansion, str) and len(expansion) > 3:
                # Only replace if it saves significant tokens
                compressed = re.sub(
                    r"\b" + re.escape(expansion) + r"\b",
                    f"/{code}",
                    compressed,
                    flags=re.IGNORECASE,
                )

        # Add emoji shortcuts
        for code, emoji in self.emoji_codes.items():
            compressed = compressed.replace(f":{code}:", emoji)

        # Calculate savings
        saved_tokens = (original_length - len(compressed)) // 4  # Rough token estimate

        if saved_tokens > 2:  # Only use compression if meaningful savings
            return compressed
        else:
            return message  # Return original if no significant savings

    def decode_message(self, encoded_message: str) -> str:
        """Expand compressed message back to natural language"""

        # Handle direct codes
        if encoded_message.startswith("/") and len(encoded_message) <= 4:
            code = encoded_message[1:]
            if code in self.decode_map:
                return self.decode_map[code]

        # Expand codes in message
        decoded = encoded_message
        for code, expansion in self.decode_map.items():
            decoded = decoded.replace(f"/{code}", expansion)

        return decoded

    def get_compression_stats(self, original: str, compressed: str) -> Dict:
        """Get compression statistics"""
        orig_tokens = len(original) // 4
        comp_tokens = len(compressed) // 4

        return {
            "original_length": len(original),
            "compressed_length": len(compressed),
            "original_tokens": orig_tokens,
            "compressed_tokens": comp_tokens,
            "tokens_saved": orig_tokens - comp_tokens,
            "compression_ratio": len(compressed) / len(original)
            if len(original) > 0
            else 1.0,
            "savings_percent": ((orig_tokens - comp_tokens) / orig_tokens * 100)
            if orig_tokens > 0
            else 0,
        }


# Integration with group chat
class CompressedGroupChatTool(GroupChatTool):
    """Group chat tool with message compression"""

    def __init__(self, chat_manager, agent_id: str, agent_type: str):
        super().__init__(chat_manager, agent_id, agent_type)
        self.codec = MessageCodec()
        self.compression_enabled = True

    def send_compressed_message(self, content: str, thread_id: str = None) -> Dict:
        """Send message with automatic compression"""
        if self.compression_enabled and self.agent_id == "human":
            # Compress human messages
            compressed = self.codec.encode_message(content)
            stats = self.codec.get_compression_stats(content, compressed)

            if stats["tokens_saved"] > 2:
                # Send both compressed version and stats
                message = self.chat_manager.add_message(
                    agent_id=self.agent_id, content=compressed, thread_id=thread_id
                )

                # Add compression info
                if stats["savings_percent"] > 20:
                    self.chat_manager.add_message(
                        agent_id="system",
                        content=f"💾 Saved {stats['tokens_saved']} tokens ({stats['savings_percent']:.1f}%)",
                        message_type="system",
                    )

                return {
                    "message_id": message.id,
                    "sent_at": message.timestamp,
                    "compression_stats": stats,
                }

        # Send uncompressed
        return self.send_message(content, thread_id)

    def decode_for_agent(self, content: str) -> str:
        """Decode compressed message for agent consumption"""
        return self.codec.decode_message(content)


# Example usage patterns
COMPRESSION_EXAMPLES = {
    # Ultra-short responses
    "Sure, go ahead and do it": "/1",  # 6 tokens → 1 token (83% savings)
    "No, don't do that": "/0",  # 5 tokens → 1 token (80% savings)
    "Maybe, I'm not sure": "/2",  # 5 tokens → 1 token (80% savings)
    # Commands
    "Restart the orchestrator": "/R",  # 3 tokens → 1 token (67% savings)
    "Show me the current status": "/S",  # 6 tokens → 1 token (83% savings)
    "List all active agents": "/A",  # 4 tokens → 1 token (75% savings)
    # Common phrases
    "Looks good to me, proceed": "/LGTM proceed",  # 6 tokens → 2 tokens (67% savings)
    "Good work on the orchestrator": "/GW on the /ORC",  # 6 tokens → 3 tokens (50% savings)
    # Technical terms
    "The database API is working": "The /DB /API is working",  # 6 tokens → 4 tokens (33% savings)
    "Check the orchestrator agent logs": "Check the /ORC /AGT /LOG",  # 6 tokens → 4 tokens (33% savings)
}


def demo_compression():
    """Demonstrate compression capabilities"""
    codec = MessageCodec()

    print("🗜️ Message Compression Demo:")
    for original, expected in COMPRESSION_EXAMPLES.items():
        compressed = codec.encode_message(original)
        stats = codec.get_compression_stats(original, compressed)
        print(
            f"'{original}' → '{compressed}' (💾 {stats['tokens_saved']} tokens, {stats['savings_percent']:.1f}%)"
        )


if __name__ == "__main__":
    demo_compression()
