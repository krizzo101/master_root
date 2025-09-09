#!/usr/bin/env python3
"""
SizeAnalyzer - GPT-5 Cost Estimation and Optimization Analysis
Provides detailed cost analysis and optimization recommendations.
Based on Phase 1 testing results showing 60-80% cost savings potential.
"""

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a session"""

    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    cost_per_interaction: float
    optimization_savings: float
    potential_savings_percent: float


@dataclass
class SizeCategory:
    """Size category information"""

    name: str
    token_range: Tuple[int, int]
    typical_cost_range: Tuple[float, float]
    optimization_priority: str
    compression_potential: float
    chunking_strategy: str


@dataclass
class OptimizationAnalysis:
    """Comprehensive optimization analysis"""

    session_id: str
    original_cost: float
    optimized_cost: float
    cost_savings: float
    savings_percent: float
    size_category: str
    optimization_score: float
    recommended_actions: List[str]
    chunking_analysis: Dict[str, Any]
    quality_impact: str


class SizeAnalyzer:
    """
    Comprehensive size and cost analysis for GPT-5 optimization.
    Provides cost estimation, optimization recommendations, and ROI analysis.
    """

    def __init__(self):
        # GPT-5 pricing (estimated based on current trends)
        self.pricing = {
            "input_per_1k": 0.025,  # $0.025 per 1K input tokens
            "output_per_1k": 0.05,  # $0.05 per 1K output tokens
            "context_per_1k": 0.01,  # $0.01 per 1K context tokens (estimated)
        }

        # Size categories based on Phase 1 testing
        self.size_categories = {
            "small": SizeCategory(
                name="Small",
                token_range=(0, 10000),
                typical_cost_range=(0.0, 0.75),
                optimization_priority="Low",
                compression_potential=1.5,
                chunking_strategy="none",
            ),
            "medium": SizeCategory(
                name="Medium",
                token_range=(10000, 50000),
                typical_cost_range=(0.75, 3.75),
                optimization_priority="Medium",
                compression_potential=2.0,
                chunking_strategy="conversation",
            ),
            "large": SizeCategory(
                name="Large",
                token_range=(50000, 200000),
                typical_cost_range=(3.75, 15.0),
                optimization_priority="High",
                compression_potential=2.5,
                chunking_strategy="adaptive",
            ),
            "extra_large": SizeCategory(
                name="Extra Large",
                token_range=(200000, float("inf")),
                typical_cost_range=(15.0, float("inf")),
                optimization_priority="Critical",
                compression_potential=3.0,
                chunking_strategy="tool_usage",
            ),
        }

        # Compression ratios from Phase 1 testing
        self.compression_ratios = {
            "conversation": 2.36,
            "tool_usage": 3.14,
            "adaptive": 2.23,
            "none": 1.0,
        }

    def analyze_session_cost(
        self, session_tokens: int, input_ratio: float = 0.6
    ) -> CostBreakdown:
        """
        Analyze cost breakdown for a session.

        Args:
            session_tokens: Total token count
            input_ratio: Ratio of input to total tokens (default 0.6 based on analysis)
        """
        input_tokens = int(session_tokens * input_ratio)
        output_tokens = session_tokens - input_tokens

        # Calculate costs
        input_cost = (input_tokens / 1000) * self.pricing["input_per_1k"]
        output_cost = (output_tokens / 1000) * self.pricing["output_per_1k"]
        total_cost = input_cost + output_cost

        # Estimate cost per interaction (assuming ~10 tokens per interaction)
        estimated_interactions = max(1, session_tokens // 10)
        cost_per_interaction = total_cost / estimated_interactions

        # Calculate optimization potential
        size_category = self.categorize_session_size(session_tokens)
        optimization_savings = self._calculate_optimization_savings(
            total_cost, size_category
        )
        potential_savings_percent = (
            (optimization_savings / total_cost * 100) if total_cost > 0 else 0
        )

        return CostBreakdown(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            cost_per_interaction=cost_per_interaction,
            optimization_savings=optimization_savings,
            potential_savings_percent=potential_savings_percent,
        )

    def categorize_session_size(self, tokens: int) -> str:
        """Categorize session by size"""
        for category_name, category in self.size_categories.items():
            min_tokens, max_tokens = category.token_range
            if min_tokens <= tokens < max_tokens:
                return category_name
        return "extra_large"

    def get_size_category_info(self, category_name: str) -> Optional[SizeCategory]:
        """Get detailed information about a size category"""
        return self.size_categories.get(category_name)

    def analyze_optimization_potential(
        self, session_tokens: int, session_data: Optional[Dict] = None
    ) -> OptimizationAnalysis:
        """
        Comprehensive optimization analysis for a session.
        """
        session_id = (
            session_data.get("session_id", "unknown") if session_data else "unknown"
        )

        # Original cost analysis
        original_cost_breakdown = self.analyze_session_cost(session_tokens)
        size_category = self.categorize_session_size(session_tokens)
        category_info = self.size_categories[size_category]

        # Optimization analysis
        best_strategy = self._recommend_chunking_strategy(session_tokens, session_data)
        compression_ratio = self.compression_ratios[best_strategy]
        optimized_tokens = int(session_tokens / compression_ratio)

        optimized_cost_breakdown = self.analyze_session_cost(optimized_tokens)
        cost_savings = (
            original_cost_breakdown.total_cost - optimized_cost_breakdown.total_cost
        )
        savings_percent = (
            (cost_savings / original_cost_breakdown.total_cost * 100)
            if original_cost_breakdown.total_cost > 0
            else 0
        )

        # Optimization score (0-100)
        optimization_score = self._calculate_optimization_score(
            session_tokens, size_category, compression_ratio, session_data
        )

        # Recommended actions
        recommended_actions = self._generate_recommendations(
            session_tokens, size_category, compression_ratio, optimization_score
        )

        # Chunking analysis
        chunking_analysis = self._analyze_chunking_options(session_tokens, session_data)

        # Quality impact assessment
        quality_impact = self._assess_quality_impact(compression_ratio, best_strategy)

        return OptimizationAnalysis(
            session_id=session_id,
            original_cost=original_cost_breakdown.total_cost,
            optimized_cost=optimized_cost_breakdown.total_cost,
            cost_savings=cost_savings,
            savings_percent=savings_percent,
            size_category=size_category,
            optimization_score=optimization_score,
            recommended_actions=recommended_actions,
            chunking_analysis=chunking_analysis,
            quality_impact=quality_impact,
        )

    def batch_analyze_costs(
        self, session_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze costs for multiple sessions.

        Args:
            session_analyses: List of session analysis data with token counts
        """
        if not session_analyses:
            return {"error": "No sessions to analyze"}

        total_cost = 0
        total_optimized_cost = 0
        total_savings = 0

        size_distribution = defaultdict(int)
        optimization_scores = []
        cost_breakdowns = []

        for session in session_analyses:
            tokens = session.get("total_tokens", 0)
            if tokens == 0:
                continue

            cost_breakdown = self.analyze_session_cost(tokens)
            optimization_analysis = self.analyze_optimization_potential(tokens, session)

            total_cost += cost_breakdown.total_cost
            total_optimized_cost += optimization_analysis.optimized_cost
            total_savings += optimization_analysis.cost_savings

            size_category = self.categorize_session_size(tokens)
            size_distribution[size_category] += 1

            optimization_scores.append(optimization_analysis.optimization_score)
            cost_breakdowns.append(cost_breakdown)

        # Calculate aggregate metrics
        avg_optimization_score = (
            statistics.mean(optimization_scores) if optimization_scores else 0
        )
        total_savings_percent = (
            (total_savings / total_cost * 100) if total_cost > 0 else 0
        )

        # ROI analysis
        roi_analysis = self._calculate_roi_analysis(
            total_cost, total_savings, len(session_analyses)
        )

        # Cost distribution analysis
        cost_distribution = self._analyze_cost_distribution(cost_breakdowns)

        return {
            "summary": {
                "total_sessions": len(session_analyses),
                "total_original_cost": round(total_cost, 2),
                "total_optimized_cost": round(total_optimized_cost, 2),
                "total_savings": round(total_savings, 2),
                "savings_percentage": round(total_savings_percent, 2),
                "average_optimization_score": round(avg_optimization_score, 2),
            },
            "size_distribution": dict(size_distribution),
            "cost_distribution": cost_distribution,
            "roi_analysis": roi_analysis,
            "optimization_recommendations": self._generate_batch_recommendations(
                session_analyses, size_distribution, avg_optimization_score
            ),
        }

    def compare_chunking_strategies(
        self, session_tokens: int, session_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Compare all chunking strategies for a session"""
        original_cost = self.analyze_session_cost(session_tokens).total_cost

        strategy_comparisons = {}

        for strategy, compression_ratio in self.compression_ratios.items():
            if strategy == "none":
                continue

            optimized_tokens = int(session_tokens / compression_ratio)
            optimized_cost = self.analyze_session_cost(optimized_tokens).total_cost
            savings = original_cost - optimized_cost
            savings_percent = (
                (savings / original_cost * 100) if original_cost > 0 else 0
            )

            # Quality assessment
            quality_impact = self._assess_quality_impact(compression_ratio, strategy)

            # Chunk count estimation
            recommended_chunks = max(1, session_tokens // 25000)
            optimized_chunks = max(1, optimized_tokens // 25000)

            strategy_comparisons[strategy] = {
                "compression_ratio": compression_ratio,
                "optimized_tokens": optimized_tokens,
                "optimized_cost": round(optimized_cost, 4),
                "cost_savings": round(savings, 4),
                "savings_percent": round(savings_percent, 2),
                "quality_impact": quality_impact,
                "recommended_chunks": recommended_chunks,
                "optimized_chunks": optimized_chunks,
                "efficiency_score": self._calculate_strategy_efficiency(
                    compression_ratio, savings_percent, quality_impact
                ),
            }

        # Recommend best strategy
        best_strategy = max(
            strategy_comparisons.items(), key=lambda x: x[1]["efficiency_score"]
        )[0]

        return {
            "original_cost": round(original_cost, 4),
            "original_tokens": session_tokens,
            "strategy_comparisons": strategy_comparisons,
            "recommended_strategy": best_strategy,
            "best_savings": strategy_comparisons[best_strategy]["cost_savings"],
            "best_compression": strategy_comparisons[best_strategy][
                "compression_ratio"
            ],
        }

    def estimate_processing_time(
        self, session_tokens: int, strategy: str = "adaptive"
    ) -> Dict[str, Any]:
        """Estimate processing time and resource usage"""
        # Base processing time estimation (tokens per second)
        base_processing_rate = 1000  # tokens/second for analysis
        chunking_overhead = 0.1  # seconds per chunk

        # Calculate chunks needed
        compression_ratio = self.compression_ratios.get(strategy, 2.23)
        optimized_tokens = int(session_tokens / compression_ratio)
        chunk_count = max(1, optimized_tokens // 25000)

        # Processing time estimation
        analysis_time = session_tokens / base_processing_rate
        chunking_time = chunk_count * chunking_overhead
        optimization_time = optimized_tokens / (
            base_processing_rate * 2
        )  # Faster for optimized
        total_time = analysis_time + chunking_time + optimization_time

        # Memory estimation (rough)
        peak_memory_mb = (session_tokens * 4) / (
            1024 * 1024
        )  # 4 bytes per token estimate
        optimized_memory_mb = peak_memory_mb / compression_ratio

        return {
            "original_tokens": session_tokens,
            "optimized_tokens": optimized_tokens,
            "chunk_count": chunk_count,
            "estimated_processing_time_seconds": round(total_time, 2),
            "estimated_processing_time_minutes": round(total_time / 60, 2),
            "peak_memory_usage_mb": round(peak_memory_mb, 2),
            "optimized_memory_usage_mb": round(optimized_memory_mb, 2),
            "memory_savings_percent": round(
                (1 - optimized_memory_mb / peak_memory_mb) * 100, 2
            ),
            "processing_phases": {
                "analysis": round(analysis_time, 2),
                "chunking": round(chunking_time, 2),
                "optimization": round(optimization_time, 2),
            },
        }

    def _calculate_optimization_savings(
        self, total_cost: float, size_category: str
    ) -> float:
        """Calculate potential optimization savings"""
        category_info = self.size_categories.get(size_category)
        if not category_info:
            return 0.0

        # Base savings from compression
        compression_potential = category_info.compression_potential
        base_savings = total_cost * (1 - 1 / compression_potential)

        # Additional savings for large sessions
        if size_category in ["large", "extra_large"]:
            base_savings *= 1.2  # 20% bonus for large sessions

        return base_savings

    def _recommend_chunking_strategy(
        self, tokens: int, session_data: Optional[Dict] = None
    ) -> str:
        """Recommend best chunking strategy"""
        size_category = self.categorize_session_size(tokens)

        # Size-based recommendations
        if size_category == "small":
            return "none"
        elif size_category == "medium":
            return "conversation"
        elif size_category == "large":
            return "adaptive"
        else:  # extra_large
            return "tool_usage"

    def _calculate_optimization_score(
        self,
        tokens: int,
        size_category: str,
        compression_ratio: float,
        session_data: Optional[Dict] = None,
    ) -> float:
        """Calculate optimization score (0-100)"""
        score = 0.0

        # Base score from size category
        size_scores = {
            "small": 20.0,
            "medium": 40.0,
            "large": 70.0,
            "extra_large": 90.0,
        }
        score += size_scores.get(size_category, 50.0)

        # Compression ratio bonus
        if compression_ratio > 3.0:
            score += 10.0
        elif compression_ratio > 2.5:
            score += 7.0
        elif compression_ratio > 2.0:
            score += 5.0

        # GPT-5 limit consideration
        if tokens > 200000:  # Exceeds practical GPT-5 limits
            score += 15.0
        elif tokens > 100000:
            score += 10.0

        # Session complexity bonus (if data available)
        if session_data:
            complexity = session_data.get("complexity_rating", "Unknown")
            if complexity in ["High", "Very High"]:
                score += 5.0

        return min(100.0, score)

    def _generate_recommendations(
        self,
        tokens: int,
        size_category: str,
        compression_ratio: float,
        optimization_score: float,
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # Size-based recommendations
        if size_category == "extra_large":
            recommendations.append(
                "CRITICAL: Session exceeds GPT-5 practical limits - immediate optimization required"
            )
            recommendations.append(
                "Use tool_usage chunking strategy for maximum compression"
            )
            recommendations.append(
                "Consider breaking into multiple optimization sessions"
            )
        elif size_category == "large":
            recommendations.append("High priority optimization candidate")
            recommendations.append(
                "Use adaptive chunking strategy for balanced compression"
            )
        elif size_category == "medium":
            recommendations.append("Moderate optimization benefits available")
            recommendations.append("Use conversation chunking to preserve context")

        # Compression-based recommendations
        if compression_ratio > 3.0:
            recommendations.append(
                f"Excellent compression potential: {compression_ratio:.1f}x reduction possible"
            )
        elif compression_ratio > 2.0:
            recommendations.append(
                f"Good compression potential: {compression_ratio:.1f}x reduction possible"
            )

        # Score-based recommendations
        if optimization_score > 80:
            recommendations.append(
                "Deploy optimization immediately for maximum cost savings"
            )
        elif optimization_score > 60:
            recommendations.append(
                "Strong candidate for optimization - deploy within next batch"
            )
        elif optimization_score > 40:
            recommendations.append(
                "Consider optimization for cost efficiency improvements"
            )

        # Cost-based recommendations
        cost_breakdown = self.analyze_session_cost(tokens)
        if cost_breakdown.total_cost > 10.0:
            recommendations.append(
                f"High cost session (${cost_breakdown.total_cost:.2f}) - prioritize optimization"
            )

        return recommendations

    def _analyze_chunking_options(
        self, tokens: int, session_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze different chunking options"""
        chunk_sizes = [10000, 15000, 20000, 25000, 30000]
        analysis = {}

        for chunk_size in chunk_sizes:
            chunk_count = max(1, tokens // chunk_size)
            overhead_tokens = chunk_count * 500  # Estimated overhead per chunk
            total_with_overhead = tokens + overhead_tokens

            analysis[f"{chunk_size}_tokens"] = {
                "chunk_count": chunk_count,
                "overhead_tokens": overhead_tokens,
                "total_tokens_with_overhead": total_with_overhead,
                "cost_with_overhead": self.analyze_session_cost(
                    total_with_overhead
                ).total_cost,
                "efficiency_rating": self._rate_chunk_efficiency(
                    chunk_size, chunk_count, tokens
                ),
            }

        # Recommend optimal chunk size
        best_option = min(analysis.items(), key=lambda x: x[1]["cost_with_overhead"])

        return {
            "chunk_options": analysis,
            "recommended_chunk_size": best_option[0],
            "optimal_chunk_count": best_option[1]["chunk_count"],
            "estimated_overhead": best_option[1]["overhead_tokens"],
        }

    def _assess_quality_impact(self, compression_ratio: float, strategy: str) -> str:
        """Assess quality impact of optimization"""
        if compression_ratio >= 3.0:
            if strategy == "tool_usage":
                return "Minimal - Technical workflows maintain quality"
            else:
                return "Moderate - High compression may affect context"
        elif compression_ratio >= 2.0:
            return "Low - Good balance of compression and quality"
        else:
            return "Minimal - Low compression preserves most context"

    def _calculate_strategy_efficiency(
        self, compression_ratio: float, savings_percent: float, quality_impact: str
    ) -> float:
        """Calculate overall strategy efficiency score"""
        efficiency = 0.0

        # Compression component (0-40 points)
        efficiency += min(40, compression_ratio * 12)

        # Savings component (0-40 points)
        efficiency += min(40, savings_percent * 0.8)

        # Quality component (0-20 points)
        quality_scores = {"Minimal": 20, "Low": 18, "Moderate": 15, "High": 10}
        quality_words = quality_impact.split(" - ")[0]
        efficiency += quality_scores.get(quality_words, 15)

        return efficiency

    def _calculate_roi_analysis(
        self, total_cost: float, total_savings: float, session_count: int
    ) -> Dict[str, Any]:
        """Calculate ROI analysis for optimization"""
        # Estimated implementation cost
        implementation_cost = 50.0  # Base cost for optimization setup
        maintenance_cost = session_count * 0.10  # $0.10 per session processing
        total_investment = implementation_cost + maintenance_cost

        # ROI calculation
        net_savings = total_savings - total_investment
        roi_percent = (
            (net_savings / total_investment * 100) if total_investment > 0 else 0
        )
        payback_period_sessions = (
            total_investment / (total_savings / session_count)
            if total_savings > 0
            else float("inf")
        )

        return {
            "total_investment": round(total_investment, 2),
            "total_savings": round(total_savings, 2),
            "net_savings": round(net_savings, 2),
            "roi_percent": round(roi_percent, 2),
            "payback_period_sessions": round(payback_period_sessions, 1)
            if payback_period_sessions != float("inf")
            else "N/A",
            "break_even": net_savings > 0,
        }

    def _analyze_cost_distribution(
        self, cost_breakdowns: List[CostBreakdown]
    ) -> Dict[str, Any]:
        """Analyze cost distribution across sessions"""
        costs = [cb.total_cost for cb in cost_breakdowns]

        if not costs:
            return {}

        return {
            "min_cost": round(min(costs), 4),
            "max_cost": round(max(costs), 4),
            "average_cost": round(statistics.mean(costs), 4),
            "median_cost": round(statistics.median(costs), 4),
            "total_cost": round(sum(costs), 2),
            "cost_ranges": {
                "under_1_dollar": len([c for c in costs if c < 1.0]),
                "1_to_5_dollars": len([c for c in costs if 1.0 <= c < 5.0]),
                "5_to_20_dollars": len([c for c in costs if 5.0 <= c < 20.0]),
                "over_20_dollars": len([c for c in costs if c >= 20.0]),
            },
        }

    def _generate_batch_recommendations(
        self,
        sessions: List[Dict],
        size_distribution: Dict[str, int],
        avg_optimization_score: float,
    ) -> List[str]:
        """Generate recommendations for batch of sessions"""
        recommendations = []

        total_sessions = len(sessions)
        critical_sessions = size_distribution.get("extra_large", 0)
        high_priority_sessions = size_distribution.get("large", 0)

        # Critical recommendations
        if critical_sessions > 0:
            recommendations.append(
                f"URGENT: {critical_sessions} sessions exceed GPT-5 limits - implement optimization immediately"
            )

        if high_priority_sessions > 0:
            recommendations.append(
                f"HIGH PRIORITY: {high_priority_sessions} large sessions have significant optimization potential"
            )

        # Batch processing recommendations
        if total_sessions > 100:
            recommendations.append(
                "Consider batch processing optimization for efficiency"
            )

        if avg_optimization_score > 70:
            recommendations.append(
                "Excellent optimization opportunity - deploy system-wide"
            )
        elif avg_optimization_score > 50:
            recommendations.append(
                "Good optimization potential - implement for high-cost sessions"
            )

        # Strategy recommendations
        tool_heavy_sessions = len(
            [s for s in sessions if s.get("tool_usage", {}).get("tool_counts", {})]
        )
        if tool_heavy_sessions > total_sessions * 0.5:
            recommendations.append(
                "Many sessions are tool-heavy - prioritize tool_usage chunking strategy"
            )

        return recommendations

    def _rate_chunk_efficiency(
        self, chunk_size: int, chunk_count: int, total_tokens: int
    ) -> str:
        """Rate efficiency of chunk configuration"""
        # Efficiency factors
        chunk_overhead_ratio = (chunk_count * 500) / total_tokens
        chunks_per_session = chunk_count

        efficiency_score = 0

        # Prefer moderate chunk counts
        if 2 <= chunks_per_session <= 10:
            efficiency_score += 3
        elif chunks_per_session <= 20:
            efficiency_score += 2
        else:
            efficiency_score += 1

        # Prefer low overhead
        if chunk_overhead_ratio < 0.1:
            efficiency_score += 3
        elif chunk_overhead_ratio < 0.2:
            efficiency_score += 2
        else:
            efficiency_score += 1

        # Prefer reasonable chunk sizes
        if 20000 <= chunk_size <= 30000:
            efficiency_score += 2
        elif 15000 <= chunk_size <= 35000:
            efficiency_score += 1

        if efficiency_score >= 7:
            return "Excellent"
        elif efficiency_score >= 5:
            return "Good"
        elif efficiency_score >= 3:
            return "Fair"
        else:
            return "Poor"
