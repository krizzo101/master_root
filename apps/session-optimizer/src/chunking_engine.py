#!/usr/bin/env python3
"""
ChunkingEngine - GPT-5 Session Chunking System
Implements 3 strategies: conversation, tool_usage, adaptive
Based on Phase 1 testing showing 2.23x-3.14x compression ratios.
"""

import json
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class ChunkResult:
    """Result from chunking operation"""

    chunks: List[Dict[str, Any]]
    strategy_used: str
    original_tokens: int
    final_tokens: int
    compression_ratio: float
    chunk_metadata: List[Dict[str, Any]]


@dataclass
class ChunkingConfig:
    """Configuration for chunking strategies"""

    max_chunk_tokens: int = 25000
    overlap_tokens: int = 1000
    preserve_conversation_flow: bool = True
    include_context_summary: bool = True
    compression_target: float = 2.0


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies"""

    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.name = self.__class__.__name__.replace("Strategy", "").lower()

    @abstractmethod
    def chunk_session(self, session_data: Dict[str, Any]) -> ChunkResult:
        """Chunk session data according to strategy"""
        pass

    def _estimate_tokens(self, content: Any) -> int:
        """Rough token estimation (1 token ≈ 4 characters)"""
        if isinstance(content, str):
            return max(1, len(content) // 4)
        elif isinstance(content, (dict, list)):
            json_str = json.dumps(content, ensure_ascii=False)
            return max(1, len(json_str) // 4)
        return 0

    def _create_context_summary(self, session_data: Dict[str, Any]) -> str:
        """Create context summary for chunk headers"""
        summary_parts = []

        # Extract basic session info
        session_id = session_data.get("session_id", "unknown")
        summary_parts.append(f"Session: {session_id}")

        # Extract project context
        if "project_name" in session_data:
            summary_parts.append(f"Project: {session_data['project_name']}")

        # Count message types
        messages = session_data.get("messages", [])
        if messages:
            user_count = len([m for m in messages if m.get("type") == "user"])
            assistant_count = len([m for m in messages if m.get("type") == "assistant"])
            summary_parts.append(
                f"Messages: {user_count} user, {assistant_count} assistant"
            )

        # Extract key topics (simple keyword extraction)
        all_content = " ".join(
            [
                str(m.get("content", ""))
                for m in messages
                if isinstance(m.get("content"), str)
            ]
        )
        keywords = self._extract_keywords(all_content)
        if keywords:
            summary_parts.append(f"Topics: {', '.join(keywords[:5])}")

        return " | ".join(summary_parts)

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract key terms from text"""
        if not text:
            return []

        # Simple keyword extraction
        text = text.lower()
        # Remove common words and focus on technical terms
        words = re.findall(r"\b[a-z_]{4,}\b", text)
        word_freq = defaultdict(int)

        # Count word frequencies
        for word in words:
            if word not in {
                "this",
                "that",
                "with",
                "from",
                "they",
                "have",
                "will",
                "been",
                "were",
                "said",
                "each",
                "which",
                "their",
                "time",
                "make",
                "like",
                "into",
                "than",
                "only",
                "other",
                "after",
                "first",
                "well",
                "also",
                "some",
                "what",
                "would",
                "there",
                "could",
                "when",
                "more",
                "very",
                "much",
                "about",
                "just",
                "then",
                "these",
                "should",
                "before",
                "through",
                "where",
                "work",
                "need",
                "want",
                "file",
                "code",
                "function",
                "message",
                "content",
                "data",
                "tool",
                "session",
            }:
                word_freq[word] += 1

        # Return most frequent technical terms
        return [
            word
            for word, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[
                :max_keywords
            ]
        ]


class ConversationStrategy(ChunkingStrategy):
    """
    Conversation-based chunking strategy.
    Preserves natural dialog flow and context.
    Target compression: 2.36x (from Phase 1 testing)
    """

    def chunk_session(self, session_data: Dict[str, Any]) -> ChunkResult:
        """
        Chunk based on conversation boundaries.
        Maintains dialog flow and context continuity.
        """
        messages = session_data.get("messages", [])
        if not messages:
            return ChunkResult([], "conversation", 0, 0, 1.0, [])

        chunks = []
        chunk_metadata = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0

        # Create session context
        context_summary = self._create_context_summary(session_data)
        context_tokens = self._estimate_tokens(context_summary)

        for i, message in enumerate(messages):
            msg_tokens = self._estimate_tokens(message)

            # Check if adding this message would exceed chunk limit
            if (
                current_tokens + msg_tokens + context_tokens
                > self.config.max_chunk_tokens
                and current_chunk
            ):
                # Find good breaking point (end of user-assistant exchange)
                break_point = self._find_conversation_break(current_chunk)

                if break_point > 0:
                    # Split at conversation break
                    chunk_messages = current_chunk[:break_point]
                    remaining_messages = current_chunk[break_point:]

                    # Create chunk with context
                    chunk = self._create_conversation_chunk(
                        chunk_messages, context_summary, chunk_index
                    )
                    chunks.append(chunk)

                    # Metadata
                    chunk_metadata.append(
                        {
                            "chunk_index": chunk_index,
                            "message_range": (
                                len(chunks) * len(chunk_messages) - len(chunk_messages),
                                len(chunks) * len(chunk_messages),
                            ),
                            "tokens": self._estimate_tokens(chunk),
                            "conversation_complete": self._is_conversation_complete(
                                chunk_messages
                            ),
                        }
                    )

                    chunk_index += 1

                    # Start new chunk with remaining messages
                    current_chunk = remaining_messages
                    current_tokens = sum(
                        self._estimate_tokens(m) for m in remaining_messages
                    )
                else:
                    # Force break if no natural boundary found
                    chunk = self._create_conversation_chunk(
                        current_chunk, context_summary, chunk_index
                    )
                    chunks.append(chunk)
                    chunk_metadata.append(
                        {
                            "chunk_index": chunk_index,
                            "message_range": (
                                len(chunks) * len(current_chunk) - len(current_chunk),
                                len(chunks) * len(current_chunk),
                            ),
                            "tokens": self._estimate_tokens(chunk),
                            "conversation_complete": False,
                        }
                    )
                    chunk_index += 1
                    current_chunk = []
                    current_tokens = 0

            # Add message to current chunk
            current_chunk.append(message)
            current_tokens += msg_tokens

        # Handle final chunk
        if current_chunk:
            chunk = self._create_conversation_chunk(
                current_chunk, context_summary, chunk_index
            )
            chunks.append(chunk)
            chunk_metadata.append(
                {
                    "chunk_index": chunk_index,
                    "message_range": (
                        len(messages) - len(current_chunk),
                        len(messages),
                    ),
                    "tokens": self._estimate_tokens(chunk),
                    "conversation_complete": True,
                }
            )

        # Calculate metrics
        original_tokens = sum(self._estimate_tokens(m) for m in messages)
        final_tokens = sum(self._estimate_tokens(c) for c in chunks)
        compression_ratio = original_tokens / final_tokens if final_tokens > 0 else 1.0

        return ChunkResult(
            chunks=chunks,
            strategy_used="conversation",
            original_tokens=original_tokens,
            final_tokens=final_tokens,
            compression_ratio=compression_ratio,
            chunk_metadata=chunk_metadata,
        )

    def _find_conversation_break(self, messages: List[Dict]) -> int:
        """Find natural conversation break point"""
        # Look for complete user-assistant exchanges
        for i in range(len(messages) - 1, 0, -1):
            if (
                messages[i - 1].get("type") == "user"
                and messages[i].get("type") == "assistant"
            ):
                return i + 1

        # Fallback: break at any user message
        for i in range(len(messages) - 1, 0, -1):
            if messages[i].get("type") == "user":
                return i

        return 0

    def _is_conversation_complete(self, messages: List[Dict]) -> bool:
        """Check if conversation chunk is complete"""
        if not messages:
            return False
        return messages[-1].get("type") == "assistant"

    def _create_conversation_chunk(
        self, messages: List[Dict], context: str, chunk_index: int
    ) -> Dict[str, Any]:
        """Create conversation chunk with context"""
        return {
            "chunk_type": "conversation",
            "chunk_index": chunk_index,
            "context_summary": context,
            "message_count": len(messages),
            "conversation_flow": self._analyze_flow(messages),
            "messages": messages,
            "timestamp": datetime.now().isoformat(),
            "optimization_metadata": {
                "strategy": "conversation",
                "preserves_context": True,
                "natural_boundaries": True,
            },
        }

    def _analyze_flow(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation flow patterns"""
        if not messages:
            return {}

        user_count = len([m for m in messages if m.get("type") == "user"])
        assistant_count = len([m for m in messages if m.get("type") == "assistant"])
        tool_count = sum(len(m.get("tool_calls", [])) for m in messages)

        return {
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "tool_interactions": tool_count,
            "flow_type": self._classify_flow_type(messages),
            "complexity": "high"
            if tool_count > 5
            else "medium"
            if tool_count > 0
            else "simple",
        }

    def _classify_flow_type(self, messages: List[Dict]) -> str:
        """Classify the type of conversation flow"""
        if not messages:
            return "unknown"

        tool_ratio = sum(len(m.get("tool_calls", [])) for m in messages) / len(messages)

        if tool_ratio > 0.5:
            return "tool_heavy"
        elif tool_ratio > 0.1:
            return "mixed_interaction"
        else:
            return "dialog_focused"


class ToolUsageStrategy(ChunkingStrategy):
    """
    Tool usage-based chunking strategy.
    Groups by tool patterns and workflows.
    Target compression: 3.14x (highest from Phase 1 testing)
    """

    def chunk_session(self, session_data: Dict[str, Any]) -> ChunkResult:
        """
        Chunk based on tool usage patterns.
        Achieves highest compression by grouping tool sequences.
        """
        messages = session_data.get("messages", [])
        if not messages:
            return ChunkResult([], "tool_usage", 0, 0, 1.0, [])

        # Analyze tool patterns
        tool_sequences = self._extract_tool_sequences(messages)

        chunks = []
        chunk_metadata = []
        chunk_index = 0

        context_summary = self._create_context_summary(session_data)

        for sequence in tool_sequences:
            if not sequence["messages"]:
                continue

            # Create tool-focused chunk
            chunk = self._create_tool_chunk(sequence, context_summary, chunk_index)
            chunks.append(chunk)

            chunk_metadata.append(
                {
                    "chunk_index": chunk_index,
                    "tool_workflow": sequence["workflow_type"],
                    "tools_used": sequence["tools_used"],
                    "message_count": len(sequence["messages"]),
                    "tokens": self._estimate_tokens(chunk),
                    "compression_efficiency": sequence["compression_potential"],
                }
            )

            chunk_index += 1

        # Handle any remaining messages (non-tool interactions)
        remaining_messages = self._get_non_tool_messages(messages, tool_sequences)
        if remaining_messages:
            chunk = self._create_dialog_chunk(
                remaining_messages, context_summary, chunk_index
            )
            chunks.append(chunk)
            chunk_metadata.append(
                {
                    "chunk_index": chunk_index,
                    "tool_workflow": "dialog_only",
                    "tools_used": [],
                    "message_count": len(remaining_messages),
                    "tokens": self._estimate_tokens(chunk),
                    "compression_efficiency": "low",
                }
            )

        # Calculate metrics
        original_tokens = sum(self._estimate_tokens(m) for m in messages)
        final_tokens = sum(self._estimate_tokens(c) for c in chunks)
        compression_ratio = original_tokens / final_tokens if final_tokens > 0 else 1.0

        return ChunkResult(
            chunks=chunks,
            strategy_used="tool_usage",
            original_tokens=original_tokens,
            final_tokens=final_tokens,
            compression_ratio=compression_ratio,
            chunk_metadata=chunk_metadata,
        )

    def _extract_tool_sequences(self, messages: List[Dict]) -> List[Dict[str, Any]]:
        """Extract tool usage sequences and classify workflows"""
        sequences = []
        current_sequence = []
        current_tools = set()

        for i, message in enumerate(messages):
            tool_calls = message.get("tool_calls", [])

            if tool_calls:
                # Add to current sequence
                current_sequence.append(message)
                for tool_call in tool_calls:
                    current_tools.add(tool_call.get("name", "unknown"))
            else:
                # End current sequence if it has tools
                if current_sequence and current_tools:
                    workflow_type = self._classify_workflow(
                        current_tools, current_sequence
                    )
                    compression_potential = self._estimate_compression(workflow_type)

                    sequences.append(
                        {
                            "messages": current_sequence.copy(),
                            "tools_used": list(current_tools),
                            "workflow_type": workflow_type,
                            "compression_potential": compression_potential,
                            "start_index": i - len(current_sequence),
                            "end_index": i,
                        }
                    )

                # Reset for next sequence
                current_sequence = [message] if message.get("type") != "user" else []
                current_tools = set()

        # Handle final sequence
        if current_sequence and current_tools:
            workflow_type = self._classify_workflow(current_tools, current_sequence)
            sequences.append(
                {
                    "messages": current_sequence,
                    "tools_used": list(current_tools),
                    "workflow_type": workflow_type,
                    "compression_potential": self._estimate_compression(workflow_type),
                    "start_index": len(messages) - len(current_sequence),
                    "end_index": len(messages),
                }
            )

        return sequences

    def _classify_workflow(self, tools: set, messages: List[Dict]) -> str:
        """Classify tool workflow type"""
        tool_categories = {
            "file_ops": {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"},
            "shell_ops": {"Bash", "mcp__shell_exec__shell_exec", "Grep", "Glob"},
            "web_ops": {"WebSearch", "WebFetch", "mcp__web_search__brave_web_search"},
            "knowledge": {
                "mcp__knowledge__knowledge_store",
                "mcp__knowledge__knowledge_query",
            },
            "planning": {"TodoWrite", "ExitPlanMode"},
            "agent": {"Task"},
        }

        workflow_scores = defaultdict(int)
        for tool in tools:
            for category, category_tools in tool_categories.items():
                if tool in category_tools:
                    workflow_scores[category] += 1

        if not workflow_scores:
            return "other"

        # Determine primary workflow
        primary = max(workflow_scores.items(), key=lambda x: x[1])[0]

        # Check for mixed workflows
        if len(workflow_scores) > 1 and list(workflow_scores.values())[1] > 0:
            return f"mixed_{primary}"

        return primary

    def _estimate_compression(self, workflow_type: str) -> str:
        """Estimate compression potential for workflow type"""
        high_compression = {
            "file_ops",
            "shell_ops",
            "mixed_file_ops",
            "mixed_shell_ops",
        }
        medium_compression = {"web_ops", "knowledge", "mixed_web_ops"}

        if workflow_type in high_compression:
            return "high"
        elif workflow_type in medium_compression:
            return "medium"
        else:
            return "low"

    def _get_non_tool_messages(
        self, messages: List[Dict], tool_sequences: List[Dict]
    ) -> List[Dict]:
        """Get messages not part of tool sequences"""
        used_indices = set()
        for seq in tool_sequences:
            used_indices.update(range(seq["start_index"], seq["end_index"]))

        return [msg for i, msg in enumerate(messages) if i not in used_indices]

    def _create_tool_chunk(
        self, sequence: Dict[str, Any], context: str, chunk_index: int
    ) -> Dict[str, Any]:
        """Create tool-focused chunk"""
        return {
            "chunk_type": "tool_workflow",
            "chunk_index": chunk_index,
            "context_summary": context,
            "workflow_type": sequence["workflow_type"],
            "tools_used": sequence["tools_used"],
            "tool_sequence_summary": self._summarize_tool_sequence(sequence),
            "messages": sequence["messages"],
            "timestamp": datetime.now().isoformat(),
            "optimization_metadata": {
                "strategy": "tool_usage",
                "compression_potential": sequence["compression_potential"],
                "workflow_efficiency": "high",
            },
        }

    def _create_dialog_chunk(
        self, messages: List[Dict], context: str, chunk_index: int
    ) -> Dict[str, Any]:
        """Create dialog-only chunk"""
        return {
            "chunk_type": "dialog",
            "chunk_index": chunk_index,
            "context_summary": context,
            "message_count": len(messages),
            "messages": messages,
            "timestamp": datetime.now().isoformat(),
            "optimization_metadata": {
                "strategy": "tool_usage",
                "compression_potential": "low",
                "workflow_efficiency": "standard",
            },
        }

    def _summarize_tool_sequence(self, sequence: Dict[str, Any]) -> str:
        """Create summary of tool sequence"""
        tools = sequence["tools_used"]
        workflow = sequence["workflow_type"]
        msg_count = len(sequence["messages"])

        return f"{workflow.title()} workflow using {len(tools)} tools ({', '.join(tools[:3])}{'...' if len(tools) > 3 else ''}) across {msg_count} operations"


class AdaptiveStrategy(ChunkingStrategy):
    """
    Adaptive chunking strategy.
    Combines conversation and tool patterns intelligently.
    Target compression: 2.23x (balanced from Phase 1 testing)
    """

    def __init__(self, config: ChunkingConfig):
        super().__init__(config)
        self.conversation_strategy = ConversationStrategy(config)
        self.tool_strategy = ToolUsageStrategy(config)

    def chunk_session(self, session_data: Dict[str, Any]) -> ChunkResult:
        """
        Adaptive chunking that selects best strategy per section.
        Balances compression with context preservation.
        """
        messages = session_data.get("messages", [])
        if not messages:
            return ChunkResult([], "adaptive", 0, 0, 1.0, [])

        # Analyze session characteristics
        session_analysis = self._analyze_session_characteristics(messages)

        # Choose primary strategy based on analysis
        if session_analysis["tool_intensity"] > 0.6:
            # High tool usage - use tool strategy
            primary_result = self.tool_strategy.chunk_session(session_data)
            fallback_result = self.conversation_strategy.chunk_session(session_data)
        elif session_analysis["conversation_flow_score"] > 0.7:
            # Strong conversation flow - use conversation strategy
            primary_result = self.conversation_strategy.chunk_session(session_data)
            fallback_result = self.tool_strategy.chunk_session(session_data)
        else:
            # Balanced - use hybrid approach
            return self._hybrid_chunk(session_data, session_analysis)

        # Use better performing strategy
        if primary_result.compression_ratio > fallback_result.compression_ratio:
            result = primary_result
        else:
            result = fallback_result

        # Update strategy name to adaptive
        result.strategy_used = "adaptive"

        # Add adaptive metadata
        for chunk in result.chunks:
            if "optimization_metadata" in chunk:
                chunk["optimization_metadata"]["adaptive_choice"] = {
                    "session_analysis": session_analysis,
                    "primary_strategy": primary_result.strategy_used,
                    "fallback_strategy": fallback_result.strategy_used,
                    "chosen_strategy": result.strategy_used,
                }

        return result

    def _analyze_session_characteristics(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze session to determine optimal chunking approach"""
        if not messages:
            return {}

        total_messages = len(messages)
        tool_messages = len([m for m in messages if m.get("tool_calls")])
        user_messages = len([m for m in messages if m.get("type") == "user"])
        assistant_messages = len([m for m in messages if m.get("type") == "assistant"])

        # Calculate metrics
        tool_intensity = tool_messages / total_messages if total_messages > 0 else 0
        dialog_balance = (
            min(user_messages, assistant_messages)
            / max(user_messages, assistant_messages)
            if max(user_messages, assistant_messages) > 0
            else 0
        )

        # Analyze tool patterns
        tool_diversity = len(
            set(
                tool_call.get("name", "")
                for msg in messages
                for tool_call in msg.get("tool_calls", [])
            )
        )

        # Analyze conversation flow
        conversation_transitions = 0
        for i in range(1, len(messages)):
            if (
                messages[i - 1].get("type") == "user"
                and messages[i].get("type") == "assistant"
            ):
                conversation_transitions += 1

        conversation_flow_score = (
            conversation_transitions / (total_messages / 2) if total_messages > 0 else 0
        )

        # Session complexity
        avg_message_size = (
            sum(self._estimate_tokens(m) for m in messages) / total_messages
            if total_messages > 0
            else 0
        )

        return {
            "total_messages": total_messages,
            "tool_intensity": tool_intensity,
            "dialog_balance": dialog_balance,
            "tool_diversity": tool_diversity,
            "conversation_flow_score": min(1.0, conversation_flow_score),
            "avg_message_size": avg_message_size,
            "complexity": self._assess_complexity(
                tool_intensity, tool_diversity, avg_message_size
            ),
        }

    def _assess_complexity(
        self, tool_intensity: float, tool_diversity: int, avg_message_size: float
    ) -> str:
        """Assess session complexity"""
        complexity_score = 0

        if tool_intensity > 0.5:
            complexity_score += 2
        elif tool_intensity > 0.2:
            complexity_score += 1

        if tool_diversity > 10:
            complexity_score += 2
        elif tool_diversity > 5:
            complexity_score += 1

        if avg_message_size > 1000:
            complexity_score += 2
        elif avg_message_size > 500:
            complexity_score += 1

        if complexity_score >= 5:
            return "very_high"
        elif complexity_score >= 3:
            return "high"
        elif complexity_score >= 1:
            return "medium"
        else:
            return "low"

    def _hybrid_chunk(
        self, session_data: Dict[str, Any], analysis: Dict[str, Any]
    ) -> ChunkResult:
        """Create hybrid chunks using both strategies"""
        messages = session_data.get("messages", [])

        # Divide session into segments
        segments = self._divide_into_segments(messages, analysis)

        chunks = []
        chunk_metadata = []
        chunk_index = 0

        context_summary = self._create_context_summary(session_data)

        for segment in segments:
            segment_data = {"messages": segment["messages"]}

            if segment["strategy"] == "tool":
                result = self.tool_strategy.chunk_session(segment_data)
            else:
                result = self.conversation_strategy.chunk_session(segment_data)

            # Add segment chunks to final result
            for chunk in result.chunks:
                chunk["chunk_index"] = chunk_index
                chunk["context_summary"] = context_summary
                chunk["segment_info"] = {
                    "strategy_choice": segment["strategy"],
                    "segment_type": segment["type"],
                    "segment_tokens": segment["tokens"],
                }
                chunks.append(chunk)

                chunk_metadata.append(
                    {
                        "chunk_index": chunk_index,
                        "segment_strategy": segment["strategy"],
                        "segment_type": segment["type"],
                        "tokens": self._estimate_tokens(chunk),
                    }
                )

                chunk_index += 1

        # Calculate final metrics
        original_tokens = sum(self._estimate_tokens(m) for m in messages)
        final_tokens = sum(self._estimate_tokens(c) for c in chunks)
        compression_ratio = original_tokens / final_tokens if final_tokens > 0 else 1.0

        return ChunkResult(
            chunks=chunks,
            strategy_used="adaptive_hybrid",
            original_tokens=original_tokens,
            final_tokens=final_tokens,
            compression_ratio=compression_ratio,
            chunk_metadata=chunk_metadata,
        )

    def _divide_into_segments(
        self, messages: List[Dict], analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Divide session into segments for hybrid processing"""
        segments = []
        current_segment = []
        current_type = None

        for message in messages:
            has_tools = bool(message.get("tool_calls"))
            msg_type = "tool" if has_tools else "conversation"

            if current_type is None:
                current_type = msg_type

            if msg_type != current_type and current_segment:
                # Finish current segment
                segments.append(
                    {
                        "messages": current_segment.copy(),
                        "type": current_type,
                        "strategy": self._choose_segment_strategy(
                            current_type, analysis
                        ),
                        "tokens": sum(
                            self._estimate_tokens(m) for m in current_segment
                        ),
                    }
                )

                # Start new segment
                current_segment = [message]
                current_type = msg_type
            else:
                current_segment.append(message)

        # Handle final segment
        if current_segment:
            segments.append(
                {
                    "messages": current_segment,
                    "type": current_type,
                    "strategy": self._choose_segment_strategy(current_type, analysis),
                    "tokens": sum(self._estimate_tokens(m) for m in current_segment),
                }
            )

        return segments

    def _choose_segment_strategy(
        self, segment_type: str, analysis: Dict[str, Any]
    ) -> str:
        """Choose best strategy for segment"""
        if segment_type == "tool":
            return "tool"
        elif analysis.get("conversation_flow_score", 0) > 0.6:
            return "conversation"
        else:
            return "conversation"  # Default for dialog segments


class ChunkingEngine:
    """
    Main chunking engine that orchestrates different strategies.
    Provides unified interface for GPT-5 payload optimization.
    """

    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()

        # Initialize strategies
        self.strategies = {
            "conversation": ConversationStrategy(self.config),
            "tool_usage": ToolUsageStrategy(self.config),
            "adaptive": AdaptiveStrategy(self.config),
        }

    def chunk_session(
        self, session_data: Dict[str, Any], strategy: str = "adaptive"
    ) -> ChunkResult:
        """
        Chunk session using specified strategy.

        Args:
            session_data: Session data to chunk
            strategy: Strategy to use ("conversation", "tool_usage", "adaptive")
        """
        if strategy not in self.strategies:
            raise ValueError(
                f"Unknown strategy: {strategy}. Available: {list(self.strategies.keys())}"
            )

        return self.strategies[strategy].chunk_session(session_data)

    def compare_strategies(
        self, session_data: Dict[str, Any]
    ) -> Dict[str, ChunkResult]:
        """Compare all strategies on the same session data"""
        results = {}

        for strategy_name, strategy in self.strategies.items():
            try:
                result = strategy.chunk_session(session_data)
                results[strategy_name] = result
            except Exception as e:
                print(f"Error with strategy {strategy_name}: {e}")
                continue

        return results

    def get_best_strategy(
        self, session_data: Dict[str, Any]
    ) -> Tuple[str, ChunkResult]:
        """Determine best strategy for given session data"""
        results = self.compare_strategies(session_data)

        if not results:
            return "adaptive", ChunkResult([], "adaptive", 0, 0, 1.0, [])

        # Choose strategy with best compression ratio
        best_strategy = max(results.items(), key=lambda x: x[1].compression_ratio)

        return best_strategy

    def batch_chunk(
        self, session_files: List[str], strategy: str = "adaptive"
    ) -> List[ChunkResult]:
        """Batch process multiple session files"""
        results = []

        for file_path in session_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    if file_path.endswith(".jsonl"):
                        # Handle Claude .jsonl format
                        session_data = {"messages": []}
                        for line in f:
                            if line.strip():
                                try:
                                    record = json.loads(line)
                                    session_data["messages"].append(record)
                                except json.JSONDecodeError:
                                    continue
                    else:
                        # Handle JSON format
                        session_data = json.load(f)

                result = self.chunk_session(session_data, strategy)
                results.append(result)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

        return results

    def analyze_chunking_effectiveness(
        self, results: List[ChunkResult]
    ) -> Dict[str, Any]:
        """Analyze effectiveness of chunking across multiple sessions"""
        if not results:
            return {"error": "No results to analyze"}

        total_original = sum(r.original_tokens for r in results)
        total_final = sum(r.final_tokens for r in results)
        avg_compression = sum(r.compression_ratio for r in results) / len(results)

        strategy_performance = defaultdict(list)
        for result in results:
            strategy_performance[result.strategy_used].append(result.compression_ratio)

        strategy_stats = {}
        for strategy, ratios in strategy_performance.items():
            strategy_stats[strategy] = {
                "count": len(ratios),
                "avg_compression": sum(ratios) / len(ratios),
                "best_compression": max(ratios),
                "worst_compression": min(ratios),
            }

        return {
            "total_sessions": len(results),
            "total_tokens_saved": total_original - total_final,
            "overall_compression_ratio": avg_compression,
            "token_reduction_percent": (
                (total_original - total_final) / total_original * 100
            )
            if total_original > 0
            else 0,
            "strategy_performance": strategy_stats,
            "sessions_by_compression": {
                "excellent": len([r for r in results if r.compression_ratio > 3.0]),
                "good": len([r for r in results if 2.0 <= r.compression_ratio <= 3.0]),
                "moderate": len(
                    [r for r in results if 1.5 <= r.compression_ratio < 2.0]
                ),
                "minimal": len([r for r in results if r.compression_ratio < 1.5]),
            },
        }
