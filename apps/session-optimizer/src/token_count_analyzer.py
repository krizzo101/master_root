#!/usr/bin/env python3
"""
TokenCountAnalyzer - GPT-5 Token Counting System
Accurate token counting using tiktoken for GPT-5 models.
Based on Phase 1 testing results showing 2.23x-3.14x compression ratios.
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import tiktoken


@dataclass
class TokenAnalysisResult:
    """Results from token analysis"""

    total_tokens: int
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    content_breakdown: Dict[str, int]
    optimization_potential: float
    size_category: str


class TokenCountAnalyzer:
    """
    Accurate token counting for GPT-5 using tiktoken.
    Handles Claude session data and provides detailed analysis.
    """

    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize with GPT-5 tokenizer.
        Note: Using gpt-4o as proxy until GPT-5 tiktoken available.
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
            self.model = model
        except KeyError:
            # Fallback to cl100k_base if model not available
            self.encoding = tiktoken.get_encoding("cl100k_base")
            self.model = "gpt-4o"

        # GPT-5 pricing (estimated based on current trends)
        self.pricing = {
            "input_per_1k": 0.025,  # $0.025 per 1K input tokens
            "output_per_1k": 0.05,  # $0.05 per 1K output tokens
        }

        # Size categories based on Phase 1 results
        self.size_categories = {
            "small": (0, 10000),
            "medium": (10000, 50000),
            "large": (50000, 200000),
            "extra_large": (200000, float("inf")),
        }

    def count_tokens(self, content: Union[str, List[Dict], Dict]) -> int:
        """
        Count tokens in content using tiktoken.
        Handles various input formats.
        """
        if isinstance(content, str):
            return len(self.encoding.encode(content))
        elif isinstance(content, (list, dict)):
            # Convert to JSON string for consistent counting
            json_str = json.dumps(content, ensure_ascii=False)
            return len(self.encoding.encode(json_str))
        else:
            return 0

    def analyze_session_tokens(self, session_data: Dict) -> TokenAnalysisResult:
        """
        Comprehensive token analysis of a session.
        Returns detailed breakdown and optimization metrics.
        """
        content_breakdown = {
            "user_messages": 0,
            "assistant_messages": 0,
            "tool_calls": 0,
            "tool_results": 0,
            "system_messages": 0,
            "metadata": 0,
        }

        total_tokens = 0
        input_tokens = 0  # User messages, tool results
        output_tokens = 0  # Assistant messages, tool calls

        # Analyze different components
        if "messages" in session_data:
            messages = session_data["messages"]
            if isinstance(messages, list):
                for message in messages:
                    msg_tokens = self.count_tokens(message)
                    total_tokens += msg_tokens

                    msg_type = message.get("type", "unknown")
                    if msg_type == "user":
                        content_breakdown["user_messages"] += msg_tokens
                        input_tokens += msg_tokens
                    elif msg_type == "assistant":
                        content_breakdown["assistant_messages"] += msg_tokens
                        output_tokens += msg_tokens
                    elif msg_type == "system":
                        content_breakdown["system_messages"] += msg_tokens
                        input_tokens += msg_tokens

        # Handle Claude .jsonl format
        elif "content" in session_data:
            content = session_data["content"]
            if isinstance(content, list):
                for item in content:
                    item_tokens = self.count_tokens(item)
                    total_tokens += item_tokens

                    if item.get("type") == "tool_use":
                        content_breakdown["tool_calls"] += item_tokens
                        output_tokens += item_tokens
                    elif item.get("type") == "tool_result":
                        content_breakdown["tool_results"] += item_tokens
                        input_tokens += item_tokens
                    else:
                        content_breakdown["assistant_messages"] += item_tokens
                        output_tokens += item_tokens

        # Handle entire session as string/object
        else:
            total_tokens = self.count_tokens(session_data)
            # Estimate 60/40 split input/output based on Phase 1 analysis
            input_tokens = int(total_tokens * 0.6)
            output_tokens = int(total_tokens * 0.4)
            content_breakdown["assistant_messages"] = total_tokens

        # Calculate costs
        estimated_cost = self._calculate_cost(input_tokens, output_tokens)

        # Determine size category
        size_category = self._categorize_size(total_tokens)

        # Calculate optimization potential based on Phase 1 results
        optimization_potential = self._calculate_optimization_potential(
            total_tokens, size_category, content_breakdown
        )

        return TokenAnalysisResult(
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
            content_breakdown=content_breakdown,
            optimization_potential=optimization_potential,
            size_category=size_category,
        )

    def analyze_message_stream(self, messages: List[Dict]) -> List[TokenAnalysisResult]:
        """
        Analyze token usage across a stream of messages.
        Useful for real-time monitoring.
        """
        results = []
        cumulative_tokens = 0

        for i, message in enumerate(messages):
            msg_tokens = self.count_tokens(message)
            cumulative_tokens += msg_tokens

            # Create analysis for this point in the stream
            session_data = {"messages": messages[: i + 1]}
            analysis = self.analyze_session_tokens(session_data)
            results.append(analysis)

        return results

    def estimate_chunking_benefit(
        self, total_tokens: int, strategy: str = "adaptive"
    ) -> Dict[str, Any]:
        """
        Estimate benefits of chunking based on Phase 1 results.
        """
        compression_ratios = {
            "conversation": 2.36,
            "tool_usage": 3.14,
            "adaptive": 2.23,
        }

        ratio = compression_ratios.get(strategy, 2.23)
        optimized_tokens = int(total_tokens / ratio)

        original_cost = self._calculate_cost(
            int(total_tokens * 0.6), int(total_tokens * 0.4)
        )
        optimized_cost = self._calculate_cost(
            int(optimized_tokens * 0.6), int(optimized_tokens * 0.4)
        )

        savings = original_cost - optimized_cost
        savings_percent = (savings / original_cost) * 100 if original_cost > 0 else 0

        return {
            "strategy": strategy,
            "original_tokens": total_tokens,
            "optimized_tokens": optimized_tokens,
            "compression_ratio": ratio,
            "original_cost": original_cost,
            "optimized_cost": optimized_cost,
            "cost_savings": savings,
            "savings_percent": savings_percent,
            "recommended_chunks": max(1, total_tokens // 25000),
        }

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on token counts"""
        input_cost = (input_tokens / 1000) * self.pricing["input_per_1k"]
        output_cost = (output_tokens / 1000) * self.pricing["output_per_1k"]
        return input_cost + output_cost

    def _categorize_size(self, tokens: int) -> str:
        """Categorize session size based on token count"""
        for category, (min_tokens, max_tokens) in self.size_categories.items():
            if min_tokens <= tokens < max_tokens:
                return category
        return "extra_large"

    def _calculate_optimization_potential(
        self, total_tokens: int, size_category: str, content_breakdown: Dict[str, int]
    ) -> float:
        """
        Calculate optimization potential (0-100) based on Phase 1 patterns.
        """
        potential = 0.0

        # Base potential by size
        size_potentials = {
            "small": 20.0,  # Minimal benefit
            "medium": 40.0,  # Moderate benefit
            "large": 70.0,  # High benefit
            "extra_large": 90.0,  # Critical benefit
        }
        potential += size_potentials.get(size_category, 50.0)

        # Adjust based on content composition
        total_content = sum(content_breakdown.values())
        if total_content > 0:
            # High tool usage = higher compression potential
            tool_ratio = (
                content_breakdown.get("tool_calls", 0)
                + content_breakdown.get("tool_results", 0)
            ) / total_content
            if tool_ratio > 0.3:  # >30% tool usage
                potential += 10.0

            # Repetitive content indicates good compression potential
            if content_breakdown.get("assistant_messages", 0) > total_content * 0.7:
                potential += 5.0

        # GPT-5 limit penalty
        if total_tokens > 200000:  # Exceeds practical GPT-5 limits
            potential += 15.0

        return min(100.0, potential)

    def batch_analyze(self, session_files: List[str]) -> List[TokenAnalysisResult]:
        """
        Analyze multiple session files efficiently.
        Memory-efficient streaming for large batches.
        """
        results = []

        for file_path in session_files:
            try:
                # Stream large files to avoid memory issues
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

                analysis = self.analyze_session_tokens(session_data)
                results.append(analysis)

            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                continue

        return results

    def get_summary_stats(self, analyses: List[TokenAnalysisResult]) -> Dict[str, Any]:
        """
        Generate summary statistics from multiple analyses.
        """
        if not analyses:
            return {"error": "No analyses provided"}

        total_tokens = sum(a.total_tokens for a in analyses)
        total_cost = sum(a.estimated_cost for a in analyses)
        avg_optimization = sum(a.optimization_potential for a in analyses) / len(
            analyses
        )

        size_distribution = {}
        for analysis in analyses:
            category = analysis.size_category
            size_distribution[category] = size_distribution.get(category, 0) + 1

        # Find sessions exceeding GPT-5 limits
        large_sessions = [a for a in analyses if a.total_tokens > 200000]

        return {
            "total_sessions": len(analyses),
            "total_tokens": total_tokens,
            "total_estimated_cost": total_cost,
            "average_tokens_per_session": total_tokens // len(analyses),
            "average_optimization_potential": avg_optimization,
            "size_distribution": size_distribution,
            "sessions_exceeding_gpt5_limits": len(large_sessions),
            "largest_session_tokens": max(a.total_tokens for a in analyses),
            "optimization_candidates": len(
                [a for a in analyses if a.optimization_potential > 70]
            ),
        }
