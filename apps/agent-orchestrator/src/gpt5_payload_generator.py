#!/usr/bin/env python3
"""
GPT-5 Payload Generation System
Converts session analytics into optimized input format for context compression.

This system provides:
- Token count analysis and estimation for GPT-5 input sizes
- Intelligent chunking strategies for large sessions
- Structured prompt generation for context optimization
- Size analysis and reporting tools
- Memory-efficient processing for large sessions
"""

import hashlib
import json
import logging
import math
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union

import tiktoken

# Import session analytics infrastructure
try:
    from analytics_components import (
        ConversationFlowExtractor,
        FileActivityExtractor,
        SessionMetricsExtractor,
        ToolUsageExtractor,
    )
    from session_analytics_engine import SessionAnalyticsEngine, SessionMetrics
except ImportError:
    logging.warning(
        "Session analytics components not available - using minimal implementations"
    )


@dataclass
class TokenAnalysis:
    """Token analysis results for GPT-5 optimization"""

    total_tokens: int
    estimated_cost: float
    compression_ratio: float
    context_efficiency_score: float
    recommended_chunks: int
    processing_time_estimate: float


@dataclass
class PayloadChunk:
    """Individual payload chunk with metadata"""

    chunk_id: str
    content: Dict[str, Any]
    token_count: int
    chunk_type: str  # 'conversation', 'tool_usage', 'file_ops', 'summary'
    overlap_tokens: int
    context_score: float
    metadata: Dict[str, Any]


@dataclass
class GPT5Payload:
    """Complete GPT-5 optimized payload"""

    session_id: str
    total_tokens: int
    chunk_count: int
    compression_ratio: float
    chunks: List[PayloadChunk]
    metadata: Dict[str, Any]
    optimization_report: TokenAnalysis
    generated_at: datetime


class TokenCountAnalyzer:
    """Accurate token counting and estimation for GPT-5"""

    def __init__(self):
        # Initialize tokenizer for GPT-4/GPT-5 (uses cl100k_base encoding)
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            logging.warning("tiktoken not available - using character-based estimation")
            self.encoding = None

        # Token cost estimates (per 1K tokens)
        self.cost_per_1k_tokens = {
            "gpt-4": 0.03,  # input cost
            "gpt-5": 0.025,  # estimated
        }

    def count_tokens(self, text: str, model: str = "gpt-5") -> int:
        """Count tokens in text for specified model"""
        if self.encoding:
            return len(self.encoding.encode(str(text)))
        else:
            # Fallback: rough character-based estimation
            return len(str(text)) // 4

    def analyze_content(
        self, content: Dict[str, Any], model: str = "gpt-5"
    ) -> TokenAnalysis:
        """Comprehensive token analysis of content"""
        # Convert content to JSON string for token counting
        content_str = json.dumps(content, ensure_ascii=False, indent=2)
        total_tokens = self.count_tokens(content_str, model)

        # Estimate cost
        estimated_cost = (total_tokens / 1000) * self.cost_per_1k_tokens.get(
            model, 0.03
        )

        # Calculate context efficiency (higher is better)
        unique_content_ratio = self._calculate_uniqueness(content_str)
        context_efficiency_score = unique_content_ratio * 100

        # Estimate optimal chunk count (8k tokens per chunk with 1k overlap)
        chunk_size = 7000  # Leave room for system prompts
        recommended_chunks = max(1, math.ceil(total_tokens / chunk_size))

        # Processing time estimate (based on token count)
        processing_time_estimate = total_tokens / 10000  # ~10k tokens per second

        return TokenAnalysis(
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            compression_ratio=1.0,  # Will be updated after compression
            context_efficiency_score=context_efficiency_score,
            recommended_chunks=recommended_chunks,
            processing_time_estimate=processing_time_estimate,
        )

    def _calculate_uniqueness(self, text: str) -> float:
        """Calculate content uniqueness ratio"""
        words = text.split()
        if not words:
            return 0.0
        unique_words = set(words)
        return len(unique_words) / len(words)


class ChunkingEngine:
    """Intelligent session segmentation for large inputs"""

    def __init__(self, chunk_size: int = 7000, overlap_size: int = 1000):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.token_analyzer = TokenCountAnalyzer()

    def chunk_by_conversation(self, session_data: Dict[str, Any]) -> List[PayloadChunk]:
        """Chunk by conversation turns with context preservation"""
        chunks = []
        messages = session_data.get("messages", [])

        current_chunk_messages = []
        current_tokens = 0
        chunk_id = 0

        for msg in messages:
            msg_tokens = self.token_analyzer.count_tokens(json.dumps(msg))

            # If adding this message would exceed chunk size, create new chunk
            if current_tokens + msg_tokens > self.chunk_size and current_chunk_messages:
                chunk = self._create_conversation_chunk(
                    chunk_id, current_chunk_messages, current_tokens
                )
                chunks.append(chunk)

                # Start new chunk with overlap
                overlap_messages = (
                    current_chunk_messages[-2:]
                    if len(current_chunk_messages) > 1
                    else current_chunk_messages
                )
                current_chunk_messages = overlap_messages + [msg]
                current_tokens = sum(
                    self.token_analyzer.count_tokens(json.dumps(m))
                    for m in current_chunk_messages
                )
                chunk_id += 1
            else:
                current_chunk_messages.append(msg)
                current_tokens += msg_tokens

        # Create final chunk if there are remaining messages
        if current_chunk_messages:
            chunk = self._create_conversation_chunk(
                chunk_id, current_chunk_messages, current_tokens
            )
            chunks.append(chunk)

        return chunks

    def chunk_by_tool_usage(self, session_data: Dict[str, Any]) -> List[PayloadChunk]:
        """Chunk by tool usage patterns"""
        chunks = []
        tool_calls = session_data.get("tool_calls", [])

        # Group tool calls by type
        tool_groups = defaultdict(list)
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "unknown")
            tool_groups[tool_name].append(tool_call)

        chunk_id = 0
        for tool_name, calls in tool_groups.items():
            content = {
                "tool_name": tool_name,
                "tool_calls": calls,
                "call_count": len(calls),
                "session_metadata": {
                    "session_id": session_data.get("session_id"),
                    "chunk_type": "tool_usage",
                },
            }

            token_count = self.token_analyzer.count_tokens(json.dumps(content))

            chunk = PayloadChunk(
                chunk_id=f"tool_{chunk_id}_{tool_name}",
                content=content,
                token_count=token_count,
                chunk_type="tool_usage",
                overlap_tokens=0,
                context_score=self._calculate_tool_context_score(calls),
                metadata={"tool_name": tool_name, "call_count": len(calls)},
            )
            chunks.append(chunk)
            chunk_id += 1

        return chunks

    def chunk_adaptively(self, session_data: Dict[str, Any]) -> List[PayloadChunk]:
        """Adaptive chunking based on content complexity"""
        # Start with conversation chunking
        conversation_chunks = self.chunk_by_conversation(session_data)

        # Add specialized chunks for high tool usage
        if session_data.get("tool_calls") and len(session_data["tool_calls"]) > 50:
            tool_chunks = self.chunk_by_tool_usage(session_data)
            conversation_chunks.extend(tool_chunks)

        # Create summary chunk
        summary_chunk = self._create_summary_chunk(session_data)
        conversation_chunks.insert(0, summary_chunk)

        return conversation_chunks

    def _create_conversation_chunk(
        self, chunk_id: int, messages: List[Dict], token_count: int
    ) -> PayloadChunk:
        """Create a conversation-based chunk"""
        content = {
            "messages": messages,
            "message_count": len(messages),
            "chunk_metadata": {
                "chunk_type": "conversation",
                "created_at": datetime.now().isoformat(),
            },
        }

        return PayloadChunk(
            chunk_id=f"conv_{chunk_id}",
            content=content,
            token_count=token_count,
            chunk_type="conversation",
            overlap_tokens=self.overlap_size if chunk_id > 0 else 0,
            context_score=self._calculate_conversation_context_score(messages),
            metadata={"message_count": len(messages)},
        )

    def _create_summary_chunk(self, session_data: Dict[str, Any]) -> PayloadChunk:
        """Create high-level summary chunk"""
        summary = {
            "session_overview": {
                "session_id": session_data.get("session_id"),
                "total_messages": len(session_data.get("messages", [])),
                "total_tool_calls": len(session_data.get("tool_calls", [])),
                "duration": session_data.get("duration_minutes", 0),
                "working_directories": list(
                    set(
                        op.get("working_dir", "")
                        for op in session_data.get("file_operations", [])
                    )
                ),
                "tools_used": list(
                    set(
                        call.get("name", "")
                        for call in session_data.get("tool_calls", [])
                    )
                ),
            }
        }

        token_count = self.token_analyzer.count_tokens(json.dumps(summary))

        return PayloadChunk(
            chunk_id="summary_0",
            content=summary,
            token_count=token_count,
            chunk_type="summary",
            overlap_tokens=0,
            context_score=100.0,  # Summary always has high context value
            metadata={"is_summary": True},
        )

    def _calculate_conversation_context_score(self, messages: List[Dict]) -> float:
        """Calculate context relevance score for conversation chunk"""
        if not messages:
            return 0.0

        # Factors: message diversity, tool usage, file operations
        unique_roles = len(set(msg.get("role", "") for msg in messages))
        has_tool_calls = any("tool_calls" in msg for msg in messages)
        has_file_ops = any("file" in str(msg).lower() for msg in messages)

        score = (
            (unique_roles * 20)
            + (30 if has_tool_calls else 0)
            + (25 if has_file_ops else 0)
        )
        return min(100.0, score)

    def _calculate_tool_context_score(self, tool_calls: List[Dict]) -> float:
        """Calculate context relevance score for tool usage chunk"""
        if not tool_calls:
            return 0.0

        # Score based on tool diversity and usage patterns
        unique_tools = len(set(call.get("name", "") for call in tool_calls))
        total_calls = len(tool_calls)

        score = min(100.0, (unique_tools * 15) + min(50, total_calls * 2))
        return score


class SessionPayloadConverter:
    """Convert session analytics to GPT-5 optimized format"""

    def __init__(self):
        self.token_analyzer = TokenCountAnalyzer()
        self.chunking_engine = ChunkingEngine()

    def convert_session(
        self, session_data: Dict[str, Any], chunking_strategy: str = "adaptive"
    ) -> GPT5Payload:
        """Convert session to optimized GPT-5 payload"""

        # Perform initial token analysis
        initial_analysis = self.token_analyzer.analyze_content(session_data)

        # Apply chunking strategy
        if chunking_strategy == "conversation":
            chunks = self.chunking_engine.chunk_by_conversation(session_data)
        elif chunking_strategy == "tool_usage":
            chunks = self.chunking_engine.chunk_by_tool_usage(session_data)
        elif chunking_strategy == "adaptive":
            chunks = self.chunking_engine.chunk_adaptively(session_data)
        else:
            raise ValueError(f"Unknown chunking strategy: {chunking_strategy}")

        # Calculate final metrics
        total_chunk_tokens = sum(chunk.token_count for chunk in chunks)
        compression_ratio = (
            initial_analysis.total_tokens / total_chunk_tokens
            if total_chunk_tokens > 0
            else 1.0
        )

        # Update analysis with compression results
        final_analysis = TokenAnalysis(
            total_tokens=total_chunk_tokens,
            estimated_cost=(total_chunk_tokens / 1000) * 0.025,  # GPT-5 estimated cost
            compression_ratio=compression_ratio,
            context_efficiency_score=initial_analysis.context_efficiency_score,
            recommended_chunks=len(chunks),
            processing_time_estimate=total_chunk_tokens / 10000,
        )

        # Create metadata
        metadata = {
            "original_session_size": initial_analysis.total_tokens,
            "chunking_strategy": chunking_strategy,
            "optimization_applied": compression_ratio < 0.9,
            "processing_stats": {
                "chunk_count": len(chunks),
                "avg_chunk_size": total_chunk_tokens / len(chunks) if chunks else 0,
                "max_chunk_size": max((c.token_count for c in chunks), default=0),
                "min_chunk_size": min((c.token_count for c in chunks), default=0),
            },
        }

        return GPT5Payload(
            session_id=session_data.get("session_id", "unknown"),
            total_tokens=total_chunk_tokens,
            chunk_count=len(chunks),
            compression_ratio=compression_ratio,
            chunks=chunks,
            metadata=metadata,
            optimization_report=final_analysis,
            generated_at=datetime.now(),
        )


class PayloadSizeAnalyzer:
    """Pre-submission size analysis and reporting"""

    def analyze_payload(self, payload: GPT5Payload) -> Dict[str, Any]:
        """Comprehensive payload analysis"""

        chunk_analysis = []
        for chunk in payload.chunks:
            chunk_analysis.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "token_count": chunk.token_count,
                    "chunk_type": chunk.chunk_type,
                    "context_score": chunk.context_score,
                    "efficiency_rating": self._calculate_efficiency_rating(chunk),
                }
            )

        # Overall analysis
        total_tokens = payload.total_tokens
        estimated_cost = payload.optimization_report.estimated_cost

        # Size categories
        size_category = self._categorize_size(total_tokens)

        # Recommendations
        recommendations = self._generate_recommendations(payload)

        return {
            "payload_summary": {
                "session_id": payload.session_id,
                "total_tokens": total_tokens,
                "chunk_count": payload.chunk_count,
                "estimated_cost": estimated_cost,
                "size_category": size_category,
                "compression_ratio": payload.compression_ratio,
            },
            "chunk_analysis": chunk_analysis,
            "efficiency_metrics": {
                "avg_context_score": sum(c.context_score for c in payload.chunks)
                / len(payload.chunks),
                "token_distribution": self._analyze_token_distribution(payload.chunks),
                "chunk_type_breakdown": self._analyze_chunk_types(payload.chunks),
            },
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def _calculate_efficiency_rating(self, chunk: PayloadChunk) -> str:
        """Rate chunk efficiency"""
        score = chunk.context_score
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"

    def _categorize_size(self, token_count: int) -> str:
        """Categorize payload size"""
        if token_count < 1000:
            return "Small"
        elif token_count < 10000:
            return "Medium"
        elif token_count < 50000:
            return "Large"
        else:
            return "Extra Large"

    def _analyze_token_distribution(
        self, chunks: List[PayloadChunk]
    ) -> Dict[str, float]:
        """Analyze how tokens are distributed across chunks"""
        token_counts = [chunk.token_count for chunk in chunks]

        return {
            "mean": sum(token_counts) / len(token_counts),
            "max": max(token_counts),
            "min": min(token_counts),
            "std_dev": self._calculate_std_dev(token_counts),
        }

    def _analyze_chunk_types(self, chunks: List[PayloadChunk]) -> Dict[str, int]:
        """Count chunks by type"""
        type_counts = defaultdict(int)
        for chunk in chunks:
            type_counts[chunk.chunk_type] += 1
        return dict(type_counts)

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) <= 1:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _generate_recommendations(self, payload: GPT5Payload) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        if payload.compression_ratio > 1.2:
            recommendations.append(
                "Consider more aggressive chunking to reduce redundancy"
            )

        if payload.chunk_count > 20:
            recommendations.append(
                "High chunk count - consider increasing chunk size for better efficiency"
            )

        low_context_chunks = [c for c in payload.chunks if c.context_score < 40]
        if len(low_context_chunks) > payload.chunk_count * 0.3:
            recommendations.append(
                "Many low-context chunks detected - review chunking strategy"
            )

        if payload.total_tokens > 100000:
            recommendations.append(
                "Large payload - consider session summarization before GPT-5 submission"
            )

        return recommendations


# Main GPT-5 Payload Generator class
class GPT5PayloadGenerator:
    """Main orchestrator for GPT-5 payload generation"""

    def __init__(self):
        self.converter = SessionPayloadConverter()
        self.size_analyzer = PayloadSizeAnalyzer()

    def generate_payload(
        self,
        session_path: str,
        chunking_strategy: str = "adaptive",
        output_format: str = "json",
    ) -> Dict[str, Any]:
        """Generate complete GPT-5 payload from session file"""

        # Load session data
        session_data = self._load_session_data(session_path)

        # Convert to payload
        payload = self.converter.convert_session(session_data, chunking_strategy)

        # Analyze payload
        analysis = self.size_analyzer.analyze_payload(payload)

        # Format output
        if output_format == "json":
            return {"payload": asdict(payload), "analysis": analysis}
        elif output_format == "structured_prompt":
            return self._format_as_structured_prompt(payload, analysis)
        else:
            raise ValueError(f"Unknown output format: {output_format}")

    def _load_session_data(self, session_path: str) -> Dict[str, Any]:
        """Load session data from file"""
        try:
            # Try to use SessionAnalyticsEngine if available
            analytics_engine = SessionAnalyticsEngine()
            session_data = analytics_engine.analyze_session(session_path)
            return session_data
        except Exception:
            # Fallback: load raw JSON data
            with open(session_path, "r") as f:
                return json.load(f)

    def _format_as_structured_prompt(
        self, payload: GPT5Payload, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format payload as structured prompt for GPT-5"""

        prompt_sections = []

        # Add summary section
        summary_chunks = [c for c in payload.chunks if c.chunk_type == "summary"]
        if summary_chunks:
            prompt_sections.append(
                {
                    "section": "session_summary",
                    "content": summary_chunks[0].content,
                    "importance": "high",
                }
            )

        # Add conversation sections
        conv_chunks = [c for c in payload.chunks if c.chunk_type == "conversation"]
        for i, chunk in enumerate(conv_chunks):
            prompt_sections.append(
                {
                    "section": f"conversation_part_{i+1}",
                    "content": chunk.content,
                    "importance": "medium" if chunk.context_score > 60 else "low",
                    "context_score": chunk.context_score,
                }
            )

        # Add tool usage sections
        tool_chunks = [c for c in payload.chunks if c.chunk_type == "tool_usage"]
        for chunk in tool_chunks:
            prompt_sections.append(
                {
                    "section": f'tool_usage_{chunk.metadata.get("tool_name", "unknown")}',
                    "content": chunk.content,
                    "importance": "medium",
                    "context_score": chunk.context_score,
                }
            )

        return {
            "structured_prompt": {
                "session_id": payload.session_id,
                "total_sections": len(prompt_sections),
                "sections": prompt_sections,
                "optimization_metadata": {
                    "total_tokens": payload.total_tokens,
                    "compression_ratio": payload.compression_ratio,
                    "recommended_processing_order": [
                        s["section"]
                        for s in sorted(
                            prompt_sections,
                            key=lambda x: x.get("context_score", 0),
                            reverse=True,
                        )
                    ],
                },
            },
            "analysis": analysis,
        }


if __name__ == "__main__":
    # Example usage
    generator = GPT5PayloadGenerator()

    # This would be used with actual session files
    # result = generator.generate_payload("session.jsonl", chunking_strategy="adaptive")
    # print(json.dumps(result, indent=2, default=str))

    print("GPT-5 Payload Generator initialized successfully!")
