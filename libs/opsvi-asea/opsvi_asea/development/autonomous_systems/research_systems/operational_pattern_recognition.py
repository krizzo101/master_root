#!/usr/bin/env python3
"""
Operational Pattern Recognition System
Advanced pattern recognition for autonomous operational improvement

This system extracts reusable patterns from operational experience to enable
autonomous improvement identification and systematic optimization.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict


class OperationalPatternRecognition:
    """Operational pattern recognition system"""

    def __init__(self):
        self.pattern_types = {
            "operational_sequences": self._extract_operational_sequences,
            "mistake_patterns": self._identify_mistake_patterns,
            "compound_learning": self._detect_compound_learning_patterns,
            "efficiency_gains": self._find_efficiency_patterns,
        }

        self.pattern_categories = {
            "high_impact": "Patterns with significant operational improvement",
            "compound_learning": "Patterns that amplify other capabilities",
            "mistake_prevention": "Patterns that prevent common failures",
            "efficiency_optimization": "Patterns that improve operational efficiency",
        }

    def analyze_operational_patterns(
        self, operational_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze operational data for patterns"""

        pattern_analysis = {
            "analysis_timestamp": datetime.now().isoformat(),
            "data_points_analyzed": len(operational_data),
            "patterns_found": {},
            "pattern_summary": {},
            "recommendations": [],
        }

        for pattern_type, analysis_func in self.pattern_types.items():
            try:
                patterns = analysis_func(operational_data)
                pattern_analysis["patterns_found"][pattern_type] = patterns
                pattern_analysis["pattern_summary"][pattern_type] = (
                    len(patterns) if isinstance(patterns, list) else 0
                )
            except Exception as e:
                pattern_analysis["patterns_found"][pattern_type] = {"error": str(e)}
                pattern_analysis["pattern_summary"][pattern_type] = 0

        # Generate recommendations based on patterns
        pattern_analysis["recommendations"] = self._generate_recommendations(
            pattern_analysis["patterns_found"]
        )

        # Calculate pattern quality metrics
        pattern_analysis["quality_metrics"] = self._calculate_pattern_quality(
            pattern_analysis["patterns_found"]
        )

        return pattern_analysis

    def _extract_operational_sequences(
        self, data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract successful operational sequences"""
        sequences = []

        # Group by context to find sequences
        context_groups = defaultdict(list)
        for item in data:
            context = item.get("context", "general")
            context_groups[context].append(item)

        for context, items in context_groups.items():
            successful_items = [item for item in items if item.get("success", False)]

            if successful_items:
                # Extract common operation patterns
                operation_patterns = []
                for item in successful_items:
                    operations = item.get("operations", [])
                    if operations:
                        operation_patterns.append(operations)

                # Find common sequences
                if operation_patterns:
                    common_sequence = self._find_common_sequence(operation_patterns)
                    if common_sequence:
                        sequence = {
                            "context": context,
                            "sequence": common_sequence,
                            "success_rate": len(successful_items) / len(items),
                            "frequency": len(successful_items),
                            "compound_learning_effect": any(
                                item.get("compound_learning", False)
                                for item in successful_items
                            ),
                            "pattern_strength": self._calculate_pattern_strength(
                                operation_patterns
                            ),
                        }
                        sequences.append(sequence)

        return sorted(
            sequences, key=lambda x: x["success_rate"] * x["frequency"], reverse=True
        )

    def _identify_mistake_patterns(
        self, data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify common mistake patterns"""
        mistake_patterns = []

        # Group failures by error type
        error_groups = defaultdict(list)
        for item in data:
            if not item.get("success", True):
                error_type = item.get("error_type", "unknown_error")
                error_groups[error_type].append(item)

        for error_type, error_items in error_groups.items():
            if len(error_items) >= 2:  # Pattern needs at least 2 occurrences
                # Extract common context and prevention methods
                contexts = [item.get("context", "") for item in error_items]
                prevention_methods = [
                    item.get("prevention", "")
                    for item in error_items
                    if item.get("prevention")
                ]

                pattern = {
                    "mistake_type": error_type,
                    "frequency": len(error_items),
                    "common_contexts": self._find_common_elements(contexts),
                    "prevention_methods": prevention_methods,
                    "impact_level": self._assess_mistake_impact(error_items),
                    "pattern_reliability": len(error_items) / max(len(data), 1),
                }
                mistake_patterns.append(pattern)

        return sorted(
            mistake_patterns,
            key=lambda x: x["frequency"] * x["impact_level"],
            reverse=True,
        )

    def _detect_compound_learning_patterns(
        self, data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect compound learning patterns"""
        compound_patterns = []

        # Find items with compound learning effects
        compound_items = [item for item in data if item.get("compound_learning", False)]

        # Group by capability combinations
        capability_groups = defaultdict(list)
        for item in compound_items:
            capabilities = tuple(sorted(item.get("capabilities", [])))
            if capabilities:
                capability_groups[capabilities].append(item)

        for capabilities, items in capability_groups.items():
            if len(items) >= 2:  # Pattern needs multiple occurrences
                amplification_effects = [
                    item.get("amplification", 1.0) for item in items
                ]
                avg_amplification = sum(amplification_effects) / len(
                    amplification_effects
                )

                pattern = {
                    "capability_combination": list(capabilities),
                    "frequency": len(items),
                    "average_amplification": avg_amplification,
                    "max_amplification": max(amplification_effects),
                    "contexts": [item.get("context", "") for item in items],
                    "reproducible": len(items)
                    >= 3,  # Consider reproducible if 3+ occurrences
                    "compound_learning_strength": self._calculate_compound_strength(
                        items
                    ),
                }
                compound_patterns.append(pattern)

        return sorted(
            compound_patterns,
            key=lambda x: x["average_amplification"] * x["frequency"],
            reverse=True,
        )

    def _find_efficiency_patterns(
        self, data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find efficiency improvement patterns"""
        efficiency_patterns = []

        # Find items with efficiency gains
        efficiency_items = [item for item in data if item.get("efficiency_gain", 0) > 0]

        # Group by improvement method
        method_groups = defaultdict(list)
        for item in efficiency_items:
            method = item.get("method", "unknown_method")
            method_groups[method].append(item)

        for method, items in method_groups.items():
            efficiency_gains = [item.get("efficiency_gain", 0) for item in items]
            avg_gain = sum(efficiency_gains) / len(efficiency_gains)

            pattern = {
                "improvement_method": method,
                "frequency": len(items),
                "average_efficiency_gain": avg_gain,
                "max_efficiency_gain": max(efficiency_gains),
                "contexts": [item.get("context", "") for item in items],
                "replicable": len(items) >= 2
                and avg_gain > 0.1,  # Replicable if 2+ occurrences and >10% gain
                "efficiency_consistency": self._calculate_efficiency_consistency(
                    efficiency_gains
                ),
            }
            efficiency_patterns.append(pattern)

        return sorted(
            efficiency_patterns,
            key=lambda x: x["average_efficiency_gain"] * x["frequency"],
            reverse=True,
        )

    def _find_common_sequence(self, operation_patterns: List[List[str]]) -> List[str]:
        """Find common sequence in operation patterns"""
        if not operation_patterns:
            return []

        # Find longest common subsequence
        common_ops = set(operation_patterns[0])
        for pattern in operation_patterns[1:]:
            common_ops &= set(pattern)

        if common_ops:
            # Return in order of first appearance
            return [op for op in operation_patterns[0] if op in common_ops]

        return []

    def _find_common_elements(self, elements: List[str]) -> List[str]:
        """Find common elements in a list of strings"""
        if not elements:
            return []

        # Split into words and find common words
        word_counts = defaultdict(int)
        for element in elements:
            words = element.lower().split()
            for word in words:
                word_counts[word] += 1

        # Return words that appear in at least half the elements
        threshold = len(elements) // 2 + 1
        return [word for word, count in word_counts.items() if count >= threshold]

    def _calculate_pattern_strength(self, patterns: List[List[str]]) -> float:
        """Calculate strength of pattern based on consistency"""
        if not patterns:
            return 0.0

        # Calculate consistency based on common elements
        all_ops = set()
        for pattern in patterns:
            all_ops.update(pattern)

        if not all_ops:
            return 0.0

        # Count how many patterns contain each operation
        op_counts = {
            op: sum(1 for pattern in patterns if op in pattern) for op in all_ops
        }

        # Calculate average consistency
        consistency_scores = [count / len(patterns) for count in op_counts.values()]
        return sum(consistency_scores) / len(consistency_scores)

    def _assess_mistake_impact(self, error_items: List[Dict[str, Any]]) -> float:
        """Assess impact level of mistake pattern"""
        impact_indicators = ["critical", "high", "severe", "major"]
        impact_scores = []

        for item in error_items:
            description = item.get("description", "").lower()
            impact_score = sum(
                1 for indicator in impact_indicators if indicator in description
            )
            impact_scores.append(impact_score)

        # Normalize to 0-1 scale
        max_possible = len(impact_indicators)
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0
        return avg_impact / max_possible

    def _calculate_compound_strength(self, items: List[Dict[str, Any]]) -> float:
        """Calculate compound learning strength"""
        amplifications = [item.get("amplification", 1.0) for item in items]

        if not amplifications:
            return 0.0

        # Consider both average amplification and consistency
        avg_amp = sum(amplifications) / len(amplifications)
        consistency = 1.0 - (max(amplifications) - min(amplifications)) / max(
            max(amplifications), 1.0
        )

        return (avg_amp - 1.0) * consistency  # Subtract 1 since 1.0 is no amplification

    def _calculate_efficiency_consistency(self, gains: List[float]) -> float:
        """Calculate consistency of efficiency gains"""
        if not gains:
            return 0.0

        avg_gain = sum(gains) / len(gains)
        variance = sum((gain - avg_gain) ** 2 for gain in gains) / len(gains)

        # Return consistency score (lower variance = higher consistency)
        return 1.0 / (1.0 + variance)

    def _calculate_pattern_quality(
        self, patterns_found: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall pattern quality metrics"""
        quality_metrics = {
            "total_patterns": 0,
            "high_quality_patterns": 0,
            "compound_learning_patterns": 0,
            "actionable_patterns": 0,
            "pattern_diversity": 0,
        }

        pattern_types_found = 0

        for pattern_type, patterns in patterns_found.items():
            if isinstance(patterns, list):
                quality_metrics["total_patterns"] += len(patterns)

                if patterns:
                    pattern_types_found += 1

                    # Count high-quality patterns (frequency >= 3 or high impact)
                    high_quality = [
                        p
                        for p in patterns
                        if p.get("frequency", 0) >= 3
                        or p.get("success_rate", 0) >= 0.8
                        or p.get("average_amplification", 1.0) > 1.5
                    ]
                    quality_metrics["high_quality_patterns"] += len(high_quality)

                    # Count compound learning patterns
                    compound = [
                        p
                        for p in patterns
                        if p.get("compound_learning_effect", False)
                        or p.get("average_amplification", 1.0) > 1.0
                    ]
                    quality_metrics["compound_learning_patterns"] += len(compound)

                    # Count actionable patterns (those with clear methods/sequences)
                    actionable = [
                        p
                        for p in patterns
                        if p.get("sequence")
                        or p.get("prevention_methods")
                        or p.get("improvement_method")
                    ]
                    quality_metrics["actionable_patterns"] += len(actionable)

        quality_metrics["pattern_diversity"] = pattern_types_found / len(
            self.pattern_types
        )

        return quality_metrics

    def _generate_recommendations(self, patterns_found: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on patterns"""
        recommendations = []

        # Analyze operational sequences
        if "operational_sequences" in patterns_found:
            sequences = patterns_found["operational_sequences"]
            if isinstance(sequences, list) and sequences:
                top_sequence = sequences[0]
                recommendations.append(
                    f"Replicate successful sequence '{' → '.join(top_sequence.get('sequence', []))}' "
                    f"(Success rate: {top_sequence.get('success_rate', 0):.1%})"
                )

        # Analyze mistake patterns
        if "mistake_patterns" in patterns_found:
            mistakes = patterns_found["mistake_patterns"]
            if isinstance(mistakes, list) and mistakes:
                top_mistake = mistakes[0]
                recommendations.append(
                    f"Implement prevention for '{top_mistake.get('mistake_type', 'unknown')}' "
                    f"(Frequency: {top_mistake.get('frequency', 0)} occurrences)"
                )

        # Analyze compound learning patterns
        if "compound_learning" in patterns_found:
            compound = patterns_found["compound_learning"]
            if isinstance(compound, list) and compound:
                top_compound = compound[0]
                capabilities = " + ".join(
                    top_compound.get("capability_combination", [])
                )
                recommendations.append(
                    f"Optimize compound learning: {capabilities} "
                    f"(Amplification: {top_compound.get('average_amplification', 1.0):.1f}x)"
                )

        # Analyze efficiency patterns
        if "efficiency_gains" in patterns_found:
            efficiency = patterns_found["efficiency_gains"]
            if isinstance(efficiency, list) and efficiency:
                top_efficiency = efficiency[0]
                recommendations.append(
                    f"Apply efficiency method '{top_efficiency.get('improvement_method', 'unknown')}' "
                    f"(Average gain: {top_efficiency.get('average_efficiency_gain', 0):.1%})"
                )

        return recommendations

    def generate_pattern_report(self, pattern_analysis: Dict[str, Any]) -> str:
        """Generate detailed pattern analysis report"""

        report = f"""
=== OPERATIONAL PATTERN RECOGNITION REPORT ===
Analysis Timestamp: {pattern_analysis['analysis_timestamp']}
Data Points Analyzed: {pattern_analysis['data_points_analyzed']}

=== PATTERN SUMMARY ===
"""

        for pattern_type, count in pattern_analysis["pattern_summary"].items():
            report += (
                f"{pattern_type.replace('_', ' ').title()}: {count} patterns found\n"
            )

        if "quality_metrics" in pattern_analysis:
            metrics = pattern_analysis["quality_metrics"]
            report += f"""
=== QUALITY METRICS ===
Total Patterns: {metrics['total_patterns']}
High Quality Patterns: {metrics['high_quality_patterns']}
Compound Learning Patterns: {metrics['compound_learning_patterns']}
Actionable Patterns: {metrics['actionable_patterns']}
Pattern Diversity: {metrics['pattern_diversity']:.1%}
"""

        if pattern_analysis["recommendations"]:
            report += "\n=== RECOMMENDATIONS ===\n"
            for i, rec in enumerate(pattern_analysis["recommendations"], 1):
                report += f"{i}. {rec}\n"

        return report


def test_operational_pattern_recognition():
    """Test the operational pattern recognition system"""

    print("=== TESTING OPERATIONAL PATTERN RECOGNITION ===")

    pattern_recognizer = OperationalPatternRecognition()

    # Test operational data
    test_data = [
        {
            "context": "database_operations",
            "operations": ["validate_query", "execute_query", "check_results"],
            "success": True,
            "compound_learning": True,
            "capabilities": ["validation", "execution"],
            "amplification": 1.5,
            "efficiency_gain": 0.3,
            "method": "query_validation",
        },
        {
            "context": "database_operations",
            "operations": ["validate_query", "execute_query", "check_results"],
            "success": True,
            "compound_learning": True,
            "capabilities": ["validation", "execution"],
            "amplification": 1.4,
            "efficiency_gain": 0.25,
            "method": "query_validation",
        },
        {
            "context": "research_operations",
            "operations": ["search", "validate", "synthesize"],
            "success": False,
            "error_type": "validation_failure",
            "description": "Critical validation failure in research synthesis",
            "prevention": "Use autonomous validation system",
        },
        {
            "context": "research_operations",
            "operations": ["search", "validate", "synthesize"],
            "success": False,
            "error_type": "validation_failure",
            "description": "Major validation failure",
            "prevention": "Implement validation checks",
        },
        {
            "context": "capability_development",
            "operations": ["research", "design", "prototype", "validate"],
            "success": True,
            "compound_learning": True,
            "capabilities": ["research", "development"],
            "amplification": 2.0,
            "efficiency_gain": 0.4,
            "method": "systematic_development",
        },
    ]

    # Analyze patterns
    pattern_analysis = pattern_recognizer.analyze_operational_patterns(test_data)

    # Generate and display report
    report = pattern_recognizer.generate_pattern_report(pattern_analysis)
    print(report)

    return pattern_analysis


def main():
    """Main execution for operational pattern recognition"""

    # Run test
    test_results = test_operational_pattern_recognition()

    print(f"\n=== PATTERN RECOGNITION PERFORMANCE ===")
    if "quality_metrics" in test_results:
        metrics = test_results["quality_metrics"]
        print(f"Total Patterns Found: {metrics['total_patterns']}")
        print(f"High Quality Patterns: {metrics['high_quality_patterns']}")
        print(f"Compound Learning Patterns: {metrics['compound_learning_patterns']}")
        print(f"Pattern Diversity: {metrics['pattern_diversity']:.1%}")

    print(f"\nRecommendations Generated: {len(test_results['recommendations'])}")
    for rec in test_results["recommendations"]:
        print(f"- {rec}")


if __name__ == "__main__":
    main()
