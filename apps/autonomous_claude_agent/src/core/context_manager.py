"""
Context Manager for optimizing token usage and context windows
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import re

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ContextItem:
    """A single item in the context"""

    content: str
    type: str  # 'system', 'user', 'assistant', 'data'
    timestamp: datetime
    tokens: int
    importance: float = 1.0
    can_compress: bool = True
    metadata: Dict[str, Any] = None


class ContextManager:
    """Manages context to optimize token usage"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_tokens = config.get("max_tokens", 8000)
        self.summarization_threshold = config.get("summarization_threshold", 6000)
        self.compression_ratio = config.get("compression_ratio", 0.3)

        self.context_items = []
        self.compressed_items = {}
        self.token_count = 0
        self.compression_cache = {}

    def add_context(
        self,
        content: str,
        item_type: str = "data",
        importance: float = 1.0,
        can_compress: bool = True,
    ) -> bool:
        """Add an item to the context"""

        tokens = self._estimate_tokens(content)

        # Check if it would exceed limits
        if self.token_count + tokens > self.max_tokens:
            logger.warning(f"Context item would exceed token limit ({tokens} tokens)")

            # Try to make room
            if not self._make_room(tokens):
                return False

        item = ContextItem(
            content=content,
            type=item_type,
            timestamp=datetime.now(),
            tokens=tokens,
            importance=importance,
            can_compress=can_compress,
        )

        self.context_items.append(item)
        self.token_count += tokens

        logger.debug(f"Added context item: {item_type} ({tokens} tokens)")
        return True

    def get_context(self, max_tokens: Optional[int] = None) -> str:
        """Get the current context as a string"""

        if max_tokens is None:
            max_tokens = self.max_tokens

        # Sort by importance and recency
        sorted_items = sorted(
            self.context_items, key=lambda x: (x.importance, x.timestamp), reverse=True
        )

        context_parts = []
        current_tokens = 0

        for item in sorted_items:
            if current_tokens + item.tokens <= max_tokens:
                context_parts.append(item.content)
                current_tokens += item.tokens
            else:
                # Try to compress and fit
                compressed = self._compress_item(item)
                compressed_tokens = self._estimate_tokens(compressed)

                if current_tokens + compressed_tokens <= max_tokens:
                    context_parts.append(compressed)
                    current_tokens += compressed_tokens

        return "\n\n".join(context_parts)

    async def compress_context(self) -> Dict[str, Any]:
        """Compress the context to reduce token usage"""

        logger.info("Compressing context...")

        initial_tokens = self.token_count
        compressed_count = 0

        # Find compressible items
        compressible = [item for item in self.context_items if item.can_compress]

        # Sort by age and size (compress old, large items first)
        compressible.sort(key=lambda x: (x.timestamp, -x.tokens))

        for item in compressible:
            if self.token_count < self.summarization_threshold:
                break

            # Compress the item
            compressed = self._compress_item(item)
            compressed_tokens = self._estimate_tokens(compressed)

            if compressed_tokens < item.tokens * 0.8:  # Only if significant reduction
                # Replace with compressed version
                item.content = compressed
                saved_tokens = item.tokens - compressed_tokens
                item.tokens = compressed_tokens
                self.token_count -= saved_tokens
                compressed_count += 1

                logger.debug(f"Compressed item: saved {saved_tokens} tokens")

        reduction = initial_tokens - self.token_count
        logger.info(
            f"Context compression complete: {compressed_count} items, {reduction} tokens saved"
        )

        return {
            "initial_tokens": initial_tokens,
            "final_tokens": self.token_count,
            "reduction": reduction,
            "items_compressed": compressed_count,
        }

    def _compress_item(self, item: ContextItem) -> str:
        """Compress a single context item"""

        # Check cache
        content_hash = hashlib.md5(item.content.encode()).hexdigest()
        if content_hash in self.compression_cache:
            return self.compression_cache[content_hash]

        compressed = item.content

        if item.type == "data":
            compressed = self._compress_data(item.content)
        elif item.type == "assistant":
            compressed = self._compress_assistant_response(item.content)
        elif item.type == "user":
            compressed = self._compress_user_input(item.content)
        else:
            compressed = self._compress_generic(item.content)

        # Cache the result
        self.compression_cache[content_hash] = compressed

        return compressed

    def _compress_data(self, content: str) -> str:
        """Compress data content"""

        # Try to parse as JSON and compress
        try:
            data = json.loads(content)

            # Remove verbose fields
            if isinstance(data, dict):
                compressed = self._compress_dict(data)
                return json.dumps(compressed, separators=(",", ":"))
            elif isinstance(data, list):
                # Keep only essential items
                if len(data) > 10:
                    compressed = data[:5] + [f"... {len(data)-10} more items ..."] + data[-5:]
                    return json.dumps(compressed, separators=(",", ":"))
        except:
            pass

        # Fall back to text compression
        return self._compress_generic(content)

    def _compress_dict(self, data: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
        """Compress a dictionary by removing verbose fields"""

        compressed = {}

        for key, value in data.items():
            # Skip metadata fields
            if key in ["metadata", "debug", "verbose", "raw"]:
                continue

            if isinstance(value, dict) and max_depth > 0:
                compressed[key] = self._compress_dict(value, max_depth - 1)
            elif isinstance(value, list) and len(value) > 5:
                compressed[key] = value[:3] + [f"... {len(value)-3} more ..."]
            elif isinstance(value, str) and len(value) > 200:
                compressed[key] = value[:100] + "..." + value[-50:]
            else:
                compressed[key] = value

        return compressed

    def _compress_assistant_response(self, content: str) -> str:
        """Compress assistant responses"""

        lines = content.split("\n")

        # Keep important lines
        important_lines = []
        for line in lines:
            # Keep lines with results, errors, or important keywords
            if any(
                keyword in line.lower()
                for keyword in ["result", "error", "success", "failed", "complete", "found"]
            ):
                important_lines.append(line)

        if len(important_lines) < len(lines) // 2:
            return "\n".join(important_lines)

        return self._compress_generic(content)

    def _compress_user_input(self, content: str) -> str:
        """Compress user input"""

        # User input is usually important, compress minimally
        if len(content) > 500:
            return content[:250] + "\n[...]\n" + content[-200:]
        return content

    def _compress_generic(self, content: str) -> str:
        """Generic text compression"""

        # Remove extra whitespace
        content = re.sub(r"\s+", " ", content)

        # Remove repetitive content
        lines = content.split(". ")
        unique_lines = []
        seen = set()

        for line in lines:
            line_hash = hashlib.md5(line.encode()).hexdigest()
            if line_hash not in seen:
                unique_lines.append(line)
                seen.add(line_hash)

        compressed = ". ".join(unique_lines)

        # Truncate if still too long
        max_length = int(len(content) * self.compression_ratio)
        if len(compressed) > max_length:
            compressed = compressed[: max_length // 2] + "\n...\n" + compressed[-max_length // 2 :]

        return compressed

    def _make_room(self, tokens_needed: int) -> bool:
        """Try to make room for new context"""

        logger.debug(f"Trying to make room for {tokens_needed} tokens")

        # Remove old, low-importance items
        self.context_items.sort(key=lambda x: (x.importance, x.timestamp))

        freed_tokens = 0
        items_removed = 0

        while freed_tokens < tokens_needed and self.context_items:
            item = self.context_items[0]

            # Don't remove high-importance items
            if item.importance > 0.8:
                break

            # Don't remove recent items (last hour)
            if datetime.now() - item.timestamp < timedelta(hours=1):
                break

            self.context_items.pop(0)
            freed_tokens += item.tokens
            items_removed += 1

        self.token_count -= freed_tokens

        if freed_tokens >= tokens_needed:
            logger.info(f"Made room by removing {items_removed} items ({freed_tokens} tokens)")
            return True

        # Try compression if removal wasn't enough
        if self.token_count > self.summarization_threshold:
            asyncio.create_task(self.compress_context())

        return False

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""

        # Rough estimation: 1 token ≈ 4 characters
        # This is a simplified estimation; in production, use tiktoken
        return len(text) // 4

    def get_statistics(self) -> Dict[str, Any]:
        """Get context statistics"""

        type_counts = {}
        for item in self.context_items:
            type_counts[item.type] = type_counts.get(item.type, 0) + 1

        return {
            "total_items": len(self.context_items),
            "total_tokens": self.token_count,
            "max_tokens": self.max_tokens,
            "usage_percent": (self.token_count / self.max_tokens) * 100,
            "type_counts": type_counts,
            "compressed_items": len(self.compressed_items),
            "cache_size": len(self.compression_cache),
        }

    def clear_old_context(self, hours: int = 24):
        """Clear context items older than specified hours"""

        cutoff = datetime.now() - timedelta(hours=hours)

        old_items = [item for item in self.context_items if item.timestamp < cutoff]
        self.context_items = [item for item in self.context_items if item.timestamp >= cutoff]

        freed_tokens = sum(item.tokens for item in old_items)
        self.token_count -= freed_tokens

        logger.info(f"Cleared {len(old_items)} old items ({freed_tokens} tokens)")

    def prioritize_context(self, goal: str):
        """Adjust importance based on current goal"""

        goal_keywords = goal.lower().split()

        for item in self.context_items:
            content_lower = item.content.lower()

            # Increase importance if related to goal
            relevance = sum(1 for keyword in goal_keywords if keyword in content_lower)
            if relevance > 0:
                item.importance = min(1.0, item.importance + relevance * 0.1)

            # Decrease importance of old items
            age = (datetime.now() - item.timestamp).total_seconds() / 3600  # Hours
            if age > 1:
                item.importance *= 0.95**age  # Exponential decay
