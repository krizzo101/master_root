#!/usr/bin/env python3
"""
PayloadGenerator - GPT-5 Structured Prompt Generator
Creates optimized prompts for GPT-5 based on chunked session data.
Implements structured templates with context preservation.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


@dataclass
class PayloadConfig:
    """Configuration for payload generation"""

    max_context_tokens: int = 15000
    include_system_prompt: bool = True
    preserve_tool_context: bool = True
    include_chunk_metadata: bool = True
    optimization_level: str = "balanced"  # "minimal", "balanced", "aggressive"
    prompt_style: str = "conversational"  # "conversational", "technical", "summary"


@dataclass
class GeneratedPayload:
    """Result from payload generation"""

    payload: Dict[str, Any]
    estimated_tokens: int
    compression_achieved: float
    payload_type: str
    metadata: Dict[str, Any]
    quality_score: float


class PromptTemplate(ABC):
    """Abstract base class for prompt templates"""

    @abstractmethod
    def generate_prompt(self, chunk_data: Dict[str, Any], config: PayloadConfig) -> str:
        """Generate prompt from chunk data"""
        pass

    @abstractmethod
    def get_system_prompt(self, config: PayloadConfig) -> str:
        """Generate system prompt"""
        pass


class ConversationalTemplate(PromptTemplate):
    """Template for conversational chunks"""

    def generate_prompt(self, chunk_data: Dict[str, Any], config: PayloadConfig) -> str:
        """Generate conversational prompt"""
        context = chunk_data.get("context_summary", "")
        messages = chunk_data.get("messages", [])

        # Build conversation flow
        conversation = []

        if config.include_chunk_metadata:
            conversation.append(f"## Session Context\n{context}\n")

        conversation.append("## Conversation Flow\n")

        for msg in messages:
            role = msg.get("type", "unknown")
            content = self._extract_content(msg)

            if role == "user":
                conversation.append(f"**User:** {content}\n")
            elif role == "assistant":
                conversation.append(f"**Assistant:** {content}\n")

                # Add tool usage if present
                if msg.get("tool_calls"):
                    tools_used = [tc.get("name", "unknown") for tc in msg["tool_calls"]]
                    conversation.append(f"*[Used tools: {', '.join(tools_used)}]*\n")

        return "\n".join(conversation)

    def get_system_prompt(self, config: PayloadConfig) -> str:
        """Generate system prompt for conversational chunks"""
        base_prompt = """You are analyzing a conversation between a user and an AI assistant. The conversation has been optimized for GPT-5 processing.

Key objectives:
1. Understand the conversation flow and context
2. Identify the main topics and tasks discussed
3. Note any tool usage patterns and their effectiveness
4. Maintain awareness of session continuity

Please provide helpful insights and continue the conversation naturally if needed."""

        if config.optimization_level == "aggressive":
            base_prompt += "\n\nFocus on extracting only the most essential information and patterns."
        elif config.optimization_level == "minimal":
            base_prompt += (
                "\n\nPreserve as much conversational context and nuance as possible."
            )

        return base_prompt

    def _extract_content(self, message: Dict[str, Any]) -> str:
        """Extract readable content from message"""
        content = message.get("content", "")

        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Handle Claude format with content blocks
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "tool_use":
                        tool_name = item.get("name", "unknown")
                        text_parts.append(f"[Using tool: {tool_name}]")
                    elif item.get("type") == "tool_result":
                        text_parts.append("[Tool result received]")
            return " ".join(text_parts)
        elif isinstance(content, dict):
            # Extract text from structured content
            return str(content.get("text", content))

        return str(content)


class TechnicalTemplate(PromptTemplate):
    """Template for technical/tool-heavy chunks"""

    def generate_prompt(self, chunk_data: Dict[str, Any], config: PayloadConfig) -> str:
        """Generate technical workflow prompt"""
        context = chunk_data.get("context_summary", "")
        workflow_type = chunk_data.get("workflow_type", "unknown")
        tools_used = chunk_data.get("tools_used", [])
        messages = chunk_data.get("messages", [])

        sections = []

        if config.include_chunk_metadata:
            sections.append(f"## Technical Workflow Analysis")
            sections.append(f"**Context:** {context}")
            sections.append(f"**Workflow Type:** {workflow_type}")
            sections.append(f"**Tools Used:** {', '.join(tools_used)}")
            sections.append("")

        # Create technical summary
        tool_sequence = self._extract_tool_sequence(messages)
        if tool_sequence:
            sections.append("## Tool Execution Sequence")
            for i, step in enumerate(tool_sequence, 1):
                sections.append(f"{i}. **{step['tool']}**: {step['description']}")
            sections.append("")

        # Add key interactions
        key_interactions = self._extract_key_interactions(messages)
        if key_interactions:
            sections.append("## Key Technical Interactions")
            for interaction in key_interactions:
                sections.append(f"- {interaction}")
            sections.append("")

        # Include critical messages if optimization level allows
        if config.optimization_level != "aggressive":
            sections.append("## Detailed Messages")
            for msg in messages:
                role = msg.get("type", "unknown")
                content = self._extract_technical_content(msg)
                if content:
                    sections.append(f"**{role.title()}:** {content}")

        return "\n".join(sections)

    def get_system_prompt(self, config: PayloadConfig) -> str:
        """Generate system prompt for technical chunks"""
        return """You are analyzing a technical workflow involving tool usage and automation. This session data has been optimized for GPT-5 processing.

Key objectives:
1. Understand the technical workflow and tool usage patterns
2. Identify the effectiveness of tool sequences
3. Note any issues or optimization opportunities in the workflow
4. Maintain technical context for complex operations

Focus on technical accuracy and workflow efficiency analysis."""

    def _extract_tool_sequence(self, messages: List[Dict]) -> List[Dict[str, str]]:
        """Extract chronological tool usage sequence"""
        sequence = []

        for msg in messages:
            if msg.get("tool_calls"):
                for tool_call in msg["tool_calls"]:
                    tool_name = tool_call.get("name", "unknown")
                    tool_input = tool_call.get("input", {})

                    # Create description based on tool type
                    description = self._describe_tool_usage(tool_name, tool_input)

                    sequence.append({"tool": tool_name, "description": description})

        return sequence

    def _describe_tool_usage(self, tool_name: str, tool_input: Dict) -> str:
        """Create human-readable description of tool usage"""
        descriptions = {
            "Read": f"Read file: {tool_input.get('file_path', 'unknown')}",
            "Write": f"Write file: {tool_input.get('file_path', 'unknown')}",
            "Edit": f"Edit file: {tool_input.get('file_path', 'unknown')}",
            "Bash": f"Execute command: {tool_input.get('command', 'unknown')}",
            "Grep": f"Search pattern: {tool_input.get('pattern', 'unknown')}",
            "WebSearch": f"Web search: {tool_input.get('query', 'unknown')}",
            "TodoWrite": "Update task list",
        }

        return descriptions.get(tool_name, f"Used {tool_name}")

    def _extract_key_interactions(self, messages: List[Dict]) -> List[str]:
        """Extract key technical interactions"""
        interactions = []

        for msg in messages:
            if msg.get("type") == "user":
                content = self._extract_technical_content(msg)
                if content and len(content) > 50:  # Substantial user input
                    interactions.append(f"User request: {content[:100]}...")
            elif msg.get("tool_calls") and msg.get("type") == "assistant":
                tool_count = len(msg["tool_calls"])
                tools = [tc.get("name", "unknown") for tc in msg["tool_calls"]]
                interactions.append(
                    f"Assistant executed {tool_count} tools: {', '.join(tools[:3])}"
                )

        return interactions[:10]  # Limit to most important

    def _extract_technical_content(self, message: Dict[str, Any]) -> str:
        """Extract technical content from message"""
        content = message.get("content", "")

        if isinstance(content, str):
            # Filter out very long outputs for optimization
            if len(content) > 2000:
                return content[:500] + "... [content truncated for optimization]"
            return content
        elif isinstance(content, list):
            # Handle Claude format
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    if len(text) > 1000:
                        text = text[:300] + "... [truncated]"
                    text_parts.append(text)
            return " ".join(text_parts)

        return str(content)[:500]


class SummaryTemplate(PromptTemplate):
    """Template for high-level summaries"""

    def generate_prompt(self, chunk_data: Dict[str, Any], config: PayloadConfig) -> str:
        """Generate summary prompt"""
        context = chunk_data.get("context_summary", "")
        messages = chunk_data.get("messages", [])

        # Extract key information
        summary_data = self._create_summary(messages, config)

        sections = []
        sections.append("## Session Summary")
        sections.append(f"**Context:** {context}")
        sections.append("")

        if summary_data["key_topics"]:
            sections.append("**Key Topics:**")
            for topic in summary_data["key_topics"]:
                sections.append(f"- {topic}")
            sections.append("")

        if summary_data["tools_used"]:
            sections.append(f"**Tools Used:** {', '.join(summary_data['tools_used'])}")
            sections.append("")

        if summary_data["key_decisions"]:
            sections.append("**Key Decisions/Actions:**")
            for decision in summary_data["key_decisions"]:
                sections.append(f"- {decision}")
            sections.append("")

        sections.append(f"**Interaction Count:** {summary_data['interaction_count']}")
        sections.append(f"**Complexity Level:** {summary_data['complexity']}")

        return "\n".join(sections)

    def get_system_prompt(self, config: PayloadConfig) -> str:
        """Generate system prompt for summary chunks"""
        return """You are analyzing a summarized session between a user and an AI assistant. This data has been heavily optimized for GPT-5 processing.

Key objectives:
1. Understand the high-level session flow and outcomes
2. Identify the main accomplishments and decisions
3. Note the overall complexity and tool usage patterns
4. Provide insights based on the summarized information

Focus on extracting insights from the condensed session data."""

    def _create_summary(
        self, messages: List[Dict], config: PayloadConfig
    ) -> Dict[str, Any]:
        """Create summary data from messages"""
        tools_used = set()
        key_topics = []
        key_decisions = []

        user_messages = []
        assistant_actions = []

        for msg in messages:
            if msg.get("type") == "user":
                content = str(msg.get("content", ""))
                user_messages.append(content)

                # Extract key topics from user messages
                topics = self._extract_topics(content)
                key_topics.extend(topics)

            elif msg.get("type") == "assistant":
                if msg.get("tool_calls"):
                    for tool_call in msg["tool_calls"]:
                        tools_used.add(tool_call.get("name", "unknown"))
                        assistant_actions.append(f"Used {tool_call.get('name')}")

                # Extract decisions from assistant responses
                content = str(msg.get("content", ""))
                decisions = self._extract_decisions(content)
                key_decisions.extend(decisions)

        # Determine complexity
        complexity = "low"
        if len(tools_used) > 10:
            complexity = "very_high"
        elif len(tools_used) > 5:
            complexity = "high"
        elif len(tools_used) > 2:
            complexity = "medium"

        return {
            "key_topics": list(set(key_topics))[:10],  # Top 10 unique topics
            "tools_used": list(tools_used),
            "key_decisions": key_decisions[:10],  # Top 10 decisions
            "interaction_count": len(messages),
            "complexity": complexity,
        }

    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics from text"""
        if not text:
            return []

        # Simple keyword extraction for topics
        text = text.lower()
        topics = []

        # Technical terms
        tech_patterns = [
            r"\b\w+\.py\b",
            r"\b\w+\.js\b",
            r"\b\w+\.md\b",  # Files
            r"\bapi\b",
            r"\bdatabase\b",
            r"\bserver\b",
            r"\bclient\b",
            r"\bfunction\b",
            r"\bclass\b",
            r"\bmethod\b",
            r"\berror\b",
            r"\bbug\b",
            r"\bfix\b",
            r"\btest\b",
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            topics.extend(matches)

        return topics[:5]  # Top 5 topics

    def _extract_decisions(self, text: str) -> List[str]:
        """Extract key decisions from text"""
        if not text:
            return []

        decisions = []

        # Look for decision indicators
        decision_patterns = [
            r"I'll\s+([^.]+)",
            r"Let me\s+([^.]+)",
            r"We should\s+([^.]+)",
            r"The solution is\s+([^.]+)",
        ]

        for pattern in decision_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            decisions.extend([match.strip() for match in matches])

        return decisions[:3]  # Top 3 decisions


class PayloadGenerator:
    """
    Main payload generator for GPT-5 optimized prompts.
    Selects appropriate templates and generates structured payloads.
    """

    def __init__(self, config: Optional[PayloadConfig] = None):
        self.config = config or PayloadConfig()

        # Initialize templates
        self.templates = {
            "conversational": ConversationalTemplate(),
            "technical": TechnicalTemplate(),
            "summary": SummaryTemplate(),
        }

    def generate_payload(
        self, chunk_data: Dict[str, Any], template_type: Optional[str] = None
    ) -> GeneratedPayload:
        """
        Generate GPT-5 payload from chunk data.

        Args:
            chunk_data: Chunked session data
            template_type: Specific template to use (auto-detect if None)
        """
        # Auto-detect template type if not specified
        if template_type is None:
            template_type = self._detect_template_type(chunk_data)

        if template_type not in self.templates:
            template_type = "conversational"  # Default fallback

        template = self.templates[template_type]

        # Generate prompt and system prompt
        prompt = template.generate_prompt(chunk_data, self.config)
        system_prompt = template.get_system_prompt(self.config)

        # Create GPT-5 payload structure
        payload = {"model": "gpt-5", "messages": []}  # Target model

        # Add system prompt if enabled
        if self.config.include_system_prompt:
            payload["messages"].append({"role": "system", "content": system_prompt})

        # Add main prompt
        payload["messages"].append({"role": "user", "content": prompt})

        # Add metadata if enabled
        if self.config.include_chunk_metadata:
            payload["metadata"] = {
                "chunk_type": chunk_data.get("chunk_type", "unknown"),
                "chunk_index": chunk_data.get("chunk_index", 0),
                "template_used": template_type,
                "optimization_level": self.config.optimization_level,
                "generation_timestamp": datetime.now().isoformat(),
                "original_message_count": len(chunk_data.get("messages", [])),
                "chunk_summary": chunk_data.get("context_summary", ""),
            }

        # Calculate metrics
        estimated_tokens = self._estimate_payload_tokens(payload)
        original_tokens = self._estimate_chunk_tokens(chunk_data)
        compression_achieved = (
            original_tokens / estimated_tokens if estimated_tokens > 0 else 1.0
        )
        quality_score = self._calculate_quality_score(
            chunk_data, payload, template_type
        )

        return GeneratedPayload(
            payload=payload,
            estimated_tokens=estimated_tokens,
            compression_achieved=compression_achieved,
            payload_type=template_type,
            metadata=payload.get("metadata", {}),
            quality_score=quality_score,
        )

    def generate_batch(self, chunks: List[Dict[str, Any]]) -> List[GeneratedPayload]:
        """Generate payloads for multiple chunks"""
        payloads = []

        for chunk in chunks:
            try:
                payload = self.generate_payload(chunk)
                payloads.append(payload)
            except Exception as e:
                print(f"Error generating payload for chunk: {e}")
                continue

        return payloads

    def create_streaming_payload(
        self, chunks: List[Dict[str, Any]], max_context_tokens: Optional[int] = None
    ) -> GeneratedPayload:
        """
        Create a single payload from multiple chunks for streaming.
        Useful for maintaining context across chunk boundaries.
        """
        max_tokens = max_context_tokens or self.config.max_context_tokens

        # Combine chunks intelligently
        combined_content = []
        current_tokens = 0

        for i, chunk in enumerate(chunks):
            chunk_tokens = self._estimate_chunk_tokens(chunk)

            if current_tokens + chunk_tokens > max_tokens and combined_content:
                break

            # Generate individual payload content
            template_type = self._detect_template_type(chunk)
            template = self.templates[template_type]
            chunk_prompt = template.generate_prompt(chunk, self.config)

            combined_content.append(
                f"## Chunk {i+1} ({template_type.title()})\n{chunk_prompt}\n"
            )
            current_tokens += chunk_tokens

        # Create combined payload
        combined_chunk = {
            "chunk_type": "streaming_combined",
            "chunks_included": len(combined_content),
            "context_summary": f"Combined context from {len(combined_content)} chunks",
            "messages": [],  # Empty since we're using combined content
        }

        # Use conversational template for combined content
        payload = {
            "model": "gpt-5",
            "messages": [
                {
                    "role": "system",
                    "content": "You are analyzing a multi-chunk session that has been optimized for GPT-5 processing. Each chunk represents a different part of the conversation or workflow.",
                },
                {"role": "user", "content": "\n".join(combined_content)},
            ],
            "metadata": {
                "chunks_combined": len(combined_content),
                "total_estimated_tokens": current_tokens,
                "generation_timestamp": datetime.now().isoformat(),
            },
        }

        return GeneratedPayload(
            payload=payload,
            estimated_tokens=current_tokens,
            compression_achieved=1.0,  # No compression in streaming
            payload_type="streaming_combined",
            metadata=payload["metadata"],
            quality_score=0.8,  # Default for combined payloads
        )

    def _detect_template_type(self, chunk_data: Dict[str, Any]) -> str:
        """Auto-detect best template type for chunk"""
        chunk_type = chunk_data.get("chunk_type", "")

        # Direct mapping from chunk types
        if chunk_type == "tool_workflow":
            return "technical"
        elif chunk_type == "conversation":
            return "conversational"
        elif chunk_type == "dialog":
            return "conversational"

        # Analyze content to determine type
        messages = chunk_data.get("messages", [])
        if not messages:
            return "summary"

        tool_count = sum(len(msg.get("tool_calls", [])) for msg in messages)
        total_messages = len(messages)

        # High tool usage = technical
        if tool_count / total_messages > 0.3:
            return "technical"

        # Check for optimization metadata
        optimization_meta = chunk_data.get("optimization_metadata", {})
        if optimization_meta.get("compression_potential") == "high":
            return "summary"

        # Default to conversational
        return "conversational"

    def _estimate_payload_tokens(self, payload: Dict[str, Any]) -> int:
        """Estimate tokens in generated payload"""
        total_chars = 0

        for message in payload.get("messages", []):
            content = message.get("content", "")
            total_chars += len(content)

        # Add metadata
        if "metadata" in payload:
            total_chars += len(json.dumps(payload["metadata"]))

        # Rough estimation: 1 token ≈ 4 characters
        return max(1, total_chars // 4)

    def _estimate_chunk_tokens(self, chunk_data: Dict[str, Any]) -> int:
        """Estimate tokens in original chunk data"""
        return max(1, len(json.dumps(chunk_data, ensure_ascii=False)) // 4)

    def _calculate_quality_score(
        self, chunk_data: Dict[str, Any], payload: Dict[str, Any], template_type: str
    ) -> float:
        """Calculate quality score for generated payload"""
        score = 0.8  # Base score

        # Bonus for appropriate template selection
        chunk_type = chunk_data.get("chunk_type", "")
        if (chunk_type == "tool_workflow" and template_type == "technical") or (
            chunk_type == "conversation" and template_type == "conversational"
        ):
            score += 0.1

        # Bonus for good compression
        original_tokens = self._estimate_chunk_tokens(chunk_data)
        payload_tokens = self._estimate_payload_tokens(payload)
        compression = original_tokens / payload_tokens if payload_tokens > 0 else 1.0

        if compression > 2.0:
            score += 0.1
        elif compression > 1.5:
            score += 0.05

        # Penalty for very large payloads
        if payload_tokens > self.config.max_context_tokens:
            score -= 0.2

        return min(1.0, max(0.0, score))

    def analyze_payload_efficiency(
        self, payloads: List[GeneratedPayload]
    ) -> Dict[str, Any]:
        """Analyze efficiency of generated payloads"""
        if not payloads:
            return {"error": "No payloads to analyze"}

        total_original = sum(
            p.compression_achieved * p.estimated_tokens for p in payloads
        )
        total_optimized = sum(p.estimated_tokens for p in payloads)

        template_usage = {}
        quality_scores = []

        for payload in payloads:
            template_usage[payload.payload_type] = (
                template_usage.get(payload.payload_type, 0) + 1
            )
            quality_scores.append(payload.quality_score)

        avg_quality = sum(quality_scores) / len(quality_scores)
        avg_compression = sum(p.compression_achieved for p in payloads) / len(payloads)

        return {
            "total_payloads": len(payloads),
            "average_compression_ratio": avg_compression,
            "average_quality_score": avg_quality,
            "total_token_savings": total_original - total_optimized,
            "template_distribution": template_usage,
            "quality_distribution": {
                "excellent": len([p for p in payloads if p.quality_score > 0.9]),
                "good": len([p for p in payloads if 0.8 <= p.quality_score <= 0.9]),
                "acceptable": len(
                    [p for p in payloads if 0.6 <= p.quality_score < 0.8]
                ),
                "poor": len([p for p in payloads if p.quality_score < 0.6]),
            },
        }
