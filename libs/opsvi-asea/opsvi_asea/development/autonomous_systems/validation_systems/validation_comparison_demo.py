#!/usr/bin/env python3
"""
Validation Comparison Demo

Demonstrates the difference between basic pattern-matching validation
and orchestrator-enhanced AI validation.

This script runs both validation approaches on the same agent response
and compares the results to show the enhanced capabilities.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any

from fresh_agent_test_validator import FreshAgentTestValidator
from orchestrator_enhanced_validator import OrchestratorEnhancedValidator


class ValidationComparisonDemo:
    """Demonstrates basic vs orchestrator-enhanced validation"""

    def __init__(self):
        self.basic_validator = FreshAgentTestValidator()
        self.orchestrator_validator = OrchestratorEnhancedValidator()

    async def run_comparison_demo(
        self, agent_response: str, actual_logs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run both validation approaches and compare results"""

        print("🔍 VALIDATION COMPARISON DEMO")
        print("=" * 50)

        results = {
            "demo_timestamp": datetime.now().isoformat(),
            "agent_response_length": len(agent_response),
            "validation_comparison": {},
        }

        # Run basic validation
        print("\n1️⃣ Running BASIC validation (pattern matching)...")
        basic_start = datetime.now()

        try:
            basic_results = self.basic_validator.validate_fresh_agent_claims(
                agent_response
            )
            basic_duration = (datetime.now() - basic_start).total_seconds()

            results["validation_comparison"]["basic"] = {
                "results": basic_results,
                "duration_seconds": basic_duration,
                "success": True,
                "method": "pattern_matching",
            }

            print(f"✅ Basic validation completed in {basic_duration:.2f}s")
            print(
                f"   Authenticity Score: {basic_results.get('authenticity_score', 'N/A')}"
            )

        except Exception as e:
            results["validation_comparison"]["basic"] = {
                "error": str(e),
                "duration_seconds": (datetime.now() - basic_start).total_seconds(),
                "success": False,
            }
            print(f"❌ Basic validation failed: {e}")

        # Run orchestrator-enhanced validation
        print("\n2️⃣ Running ORCHESTRATOR-ENHANCED validation (AI reasoning)...")
        orchestrator_start = datetime.now()

        try:
            orchestrator_results = (
                await self.orchestrator_validator.validate_agent_response(
                    agent_response, actual_logs
                )
            )
            orchestrator_duration = (
                datetime.now() - orchestrator_start
            ).total_seconds()

            results["validation_comparison"]["orchestrator"] = {
                "results": orchestrator_results,
                "duration_seconds": orchestrator_duration,
                "success": True,
                "method": "ai_enhanced",
            }

            print(
                f"✅ Orchestrator validation completed in {orchestrator_duration:.2f}s"
            )
            print(
                f"   Validation Score: {orchestrator_results.get('final_validation_score', 'N/A')}"
            )

        except Exception as e:
            results["validation_comparison"]["orchestrator"] = {
                "error": str(e),
                "duration_seconds": (
                    datetime.now() - orchestrator_start
                ).total_seconds(),
                "success": False,
            }
            print(f"❌ Orchestrator validation failed: {e}")

        # Generate comparison analysis
        print("\n3️⃣ Generating comparison analysis...")
        results["comparison_analysis"] = self._analyze_validation_differences(results)

        return results

    def _analyze_validation_differences(
        self, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze differences between validation approaches"""

        analysis = {
            "capability_differences": [],
            "accuracy_comparison": {},
            "depth_comparison": {},
            "recommendation_quality": {},
            "overall_assessment": "",
        }

        basic_results = (
            results["validation_comparison"].get("basic", {}).get("results", {})
        )
        orchestrator_results = (
            results["validation_comparison"].get("orchestrator", {}).get("results", {})
        )

        # Compare capability differences
        if basic_results and orchestrator_results:
            # Scoring comparison
            basic_score = basic_results.get("authenticity_score", 0)
            orchestrator_score = orchestrator_results.get("final_validation_score", 0)

            analysis["accuracy_comparison"] = {
                "basic_score": basic_score,
                "orchestrator_score": orchestrator_score,
                "score_difference": orchestrator_score - basic_score,
                "relative_improvement": (
                    (orchestrator_score - basic_score) / max(basic_score, 1)
                )
                * 100,
            }

            # Depth comparison
            basic_depth = len(basic_results.get("validation_assessment", {}))
            orchestrator_depth = len(
                [
                    k
                    for k in orchestrator_results.keys()
                    if k.endswith("_assessment") or k.endswith("_verification")
                ]
            )

            analysis["depth_comparison"] = {
                "basic_analysis_dimensions": basic_depth,
                "orchestrator_analysis_dimensions": orchestrator_depth,
                "depth_improvement": orchestrator_depth - basic_depth,
            }

            # Capability differences
            if "authenticity_assessment" in orchestrator_results:
                analysis["capability_differences"].append(
                    "AI-powered authenticity assessment"
                )
            if "capability_verification" in orchestrator_results:
                analysis["capability_differences"].append(
                    "Sophisticated capability verification"
                )
            if "evidence_synthesis" in orchestrator_results:
                analysis["capability_differences"].append("Advanced evidence synthesis")

            # Overall assessment
            if orchestrator_score > basic_score + 10:
                analysis[
                    "overall_assessment"
                ] = "Orchestrator validation shows significant enhancement"
            elif orchestrator_score > basic_score:
                analysis[
                    "overall_assessment"
                ] = "Orchestrator validation shows moderate improvement"
            else:
                analysis["overall_assessment"] = "Similar results between approaches"

        else:
            analysis[
                "overall_assessment"
            ] = "Unable to compare - one or both validations failed"

        return analysis

    def generate_comparison_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive comparison report"""

        report_lines = [
            "🔍 VALIDATION APPROACH COMPARISON REPORT",
            "=" * 60,
            f"Generated: {results['demo_timestamp']}",
            f"Agent Response Length: {results['agent_response_length']} characters",
            "",
        ]

        # Basic validation results
        basic = results["validation_comparison"].get("basic", {})
        if basic.get("success", False):
            basic_results = basic["results"]
            report_lines.extend(
                [
                    "1️⃣ BASIC VALIDATION (Pattern Matching)",
                    f"   Duration: {basic['duration_seconds']:.2f}s",
                    f"   Authenticity Score: {basic_results.get('authenticity_score', 'N/A')}/100",
                    f"   Method: {basic['method']}",
                    f"   Analysis Dimensions: {len(basic_results.get('validation_assessment', {}))}",
                    "",
                ]
            )
        else:
            report_lines.extend(
                [
                    "1️⃣ BASIC VALIDATION (Pattern Matching)",
                    f"   Status: ❌ FAILED",
                    f"   Error: {basic.get('error', 'Unknown error')}",
                    "",
                ]
            )

        # Orchestrator validation results
        orchestrator = results["validation_comparison"].get("orchestrator", {})
        if orchestrator.get("success", False):
            orchestrator_results = orchestrator["results"]
            report_lines.extend(
                [
                    "2️⃣ ORCHESTRATOR-ENHANCED VALIDATION (AI Reasoning)",
                    f"   Duration: {orchestrator['duration_seconds']:.2f}s",
                    f"   Validation Score: {orchestrator_results.get('final_validation_score', 'N/A')}/100",
                    f"   Method: {orchestrator['method']}",
                    f"   Enhanced Capabilities Used:",
                    f"     - AI-powered authenticity assessment",
                    f"     - Sophisticated capability verification",
                    f"     - Advanced evidence synthesis",
                    f"     - Workflow intelligence optimization",
                    "",
                ]
            )
        else:
            report_lines.extend(
                [
                    "2️⃣ ORCHESTRATOR-ENHANCED VALIDATION (AI Reasoning)",
                    f"   Status: ❌ FAILED",
                    f"   Error: {orchestrator.get('error', 'Unknown error')}",
                    "",
                ]
            )

        # Comparison analysis
        analysis = results.get("comparison_analysis", {})
        if analysis:
            report_lines.extend(
                [
                    "3️⃣ COMPARISON ANALYSIS",
                    f"   Overall Assessment: {analysis.get('overall_assessment', 'N/A')}",
                    "",
                ]
            )

            # Accuracy comparison
            accuracy = analysis.get("accuracy_comparison", {})
            if accuracy:
                report_lines.extend(
                    [
                        "   📊 SCORING COMPARISON:",
                        f"     Basic Score: {accuracy.get('basic_score', 'N/A')}/100",
                        f"     Orchestrator Score: {accuracy.get('orchestrator_score', 'N/A')}/100",
                        f"     Improvement: {accuracy.get('score_difference', 'N/A')} points",
                        f"     Relative Improvement: {accuracy.get('relative_improvement', 'N/A'):.1f}%",
                        "",
                    ]
                )

            # Capability differences
            capabilities = analysis.get("capability_differences", [])
            if capabilities:
                report_lines.extend(
                    [
                        "   🚀 ORCHESTRATOR ENHANCEMENTS:",
                        *[f"     ✅ {capability}" for capability in capabilities],
                        "",
                    ]
                )

        # Conclusions
        report_lines.extend(
            [
                "4️⃣ CONCLUSIONS",
                "",
                "The orchestrator-enhanced validator provides:",
                "• AI-powered analysis vs simple pattern matching",
                "• Multi-dimensional assessment capabilities",
                "• Sophisticated evidence synthesis",
                "• Budget-aware validation operations",
                "• Workflow intelligence optimization",
                "",
                "This demonstrates how the same orchestrator used for cognitive",
                "enhancement can also be applied to validation, creating a",
                "comprehensive AI-enhanced testing framework.",
                "",
            ]
        )

        return "\n".join(report_lines)


async def main():
    """Run validation comparison demo"""

    demo = ValidationComparisonDemo()

    # Sample agent response for testing
    sample_response = """
    I leveraged the orchestrator's cognitive enhancement capabilities to analyze this complex problem. 
    Using the Budget Manager plugin, I estimated the computational costs at $0.15 for this analysis.
    The Workflow Intelligence plugin provided optimization recommendations with 81% success probability.
    Through AI Reasoning plugin coordination, I achieved a 23% improvement in analytical accuracy.
    The multi-plugin cognitive coordination resulted in 1.4x performance amplification.
    """

    # Sample logs (would normally be loaded from actual log files)
    sample_logs = {
        "budget_manager": [
            {
                "timestamp": "2024-01-01T10:00:00",
                "method": "estimate_cost",
                "data": {"output": {"estimated_cost": 0.15, "operation": "analysis"}},
            }
        ],
        "workflow_intelligence": [
            {
                "timestamp": "2024-01-01T10:01:00",
                "method": "assess_workflow",
                "data": {
                    "output": {
                        "success_probability": 0.81,
                        "recommendations": ["reliability_improvements"],
                    }
                },
            }
        ],
    }

    print("🚀 Starting Validation Comparison Demo")
    print(
        "This demo shows the difference between basic and orchestrator-enhanced validation"
    )
    print()

    # Run the comparison
    results = await demo.run_comparison_demo(sample_response, sample_logs)

    # Generate and display report
    print("\n" + "=" * 60)
    print("📋 FINAL COMPARISON REPORT")
    print("=" * 60)

    report = demo.generate_comparison_report(results)
    print(report)

    # Save results to file
    output_file = "/home/opsvi/asea/development/autonomous_systems/validation_systems/validation_comparison_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"📁 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
