#!/usr/bin/env python3
"""
Fresh Agent Test Scenario - Real Cognitive Enhancement

This demonstrates what a fresh agent will experience when using the cognitive enhancement.
Run this to show the difference between standard vs enhanced approaches.
"""

from cognitive_enhancement_orchestrator import (
    enhance_decision_making,
)


def test_scenario_for_fresh_agent():
    """
    Test scenario: E-commerce platform architecture decision

    This is what a fresh agent will be asked to solve, with and without cognitive enhancement.
    """

    print("🧪 FRESH AGENT TEST SCENARIO")
    print("=" * 60)
    print("SCENARIO: E-commerce platform experiencing performance issues")
    print("BUDGET: $50,000 | TIMELINE: 3 months | PEAK SEASON: Approaching")
    print("QUESTION: Optimize current system or rebuild with microservices?")
    print("=" * 60)

    # Complex decision context that will benefit from cognitive enhancement
    decision_context = {
        "objective": "Choose optimal e-commerce platform architecture strategy",
        "decision_options": [
            {
                "name": "Optimize existing monolithic system",
                "estimated_cost": 20000,
                "timeline": "6-8 weeks",
                "success_probability": 0.75,
                "benefits": ["Faster implementation", "Lower risk", "Immediate gains"],
                "risks": [
                    "Limited scalability",
                    "Technical debt",
                    "Performance ceiling",
                ],
            },
            {
                "name": "Rebuild with microservices",
                "estimated_cost": 45000,
                "timeline": "12-14 weeks",
                "success_probability": 0.65,
                "benefits": ["Modern architecture", "Scalability", "Future-proof"],
                "risks": ["Higher complexity", "Longer timeline", "Learning curve"],
            },
            {
                "name": "Hybrid approach",
                "estimated_cost": 35000,
                "timeline": "10-12 weeks",
                "success_probability": 0.70,
                "benefits": [
                    "Balanced approach",
                    "Gradual migration",
                    "Risk mitigation",
                ],
                "risks": ["Architectural inconsistency", "Coordination overhead"],
            },
        ],
        "constraints": {
            "budget_limit": 50000,
            "timeline_limit": "12 weeks",
            "team_size": 6,
            "peak_season_deadline": "8 weeks",
        },
        "success_criteria": [
            "Handle 3x current peak traffic",
            "Reduce response time by 50%",
            "Maintain 99.9% uptime during peak season",
            "Stay within budget and timeline",
        ],
        "business_impact": {
            "revenue_at_risk": "30% of annual revenue during peak season",
            "customer_complaints": "Increasing about slow checkout",
            "competitive_pressure": "High - competitors have faster sites",
        },
    }

    print("\n🤖 TESTING COGNITIVE ENHANCEMENT...")

    # Test cognitive enhancement (what fresh agent will use)
    enhanced_result = enhance_decision_making(decision_context)

    print(
        f"\n✅ Enhancement Status: {enhanced_result.get('cognitive_enhancement_applied', False)}"
    )

    if enhanced_result.get("cognitive_enhancement_applied", False):
        print(
            f"🧠 Cognitive Pipeline Used: {enhanced_result.get('cognitive_pipeline_used', [])}"
        )

        # Show what each cognitive plugin provides
        pre_analysis = enhanced_result.get("pre_analysis", {})
        if pre_analysis:
            print("\n🔍 PRE-ANALYSIS INSIGHTS:")
            print(f"   Core Intent: {pre_analysis.get('core_intent', 'N/A')}")
            print(f"   Complexity: {pre_analysis.get('complexity_level', 'N/A')}")
            print(
                f"   Research Priorities: {pre_analysis.get('research_priorities', [])}"
            )

        ai_reasoning = enhanced_result.get("ai_reasoning", {})
        if ai_reasoning:
            print("\n🤖 AI REASONING:")
            reasoning_text = ai_reasoning.get("reasoning", "N/A")
            print(
                f"   {reasoning_text[:200]}..."
                if len(reasoning_text) > 200
                else reasoning_text
            )

        quality_critique = enhanced_result.get("quality_critique", {})
        if quality_critique:
            print("\n🎯 QUALITY CRITIQUE:")
            print(
                f"   Quality Score: {quality_critique.get('quality_score', 'N/A')}/10"
            )
            print(f"   Needs Revision: {quality_critique.get('needs_revision', 'N/A')}")
            improvements = quality_critique.get("improvement_suggestions", [])
            if improvements:
                print(f"   Improvements: {improvements[:2]}")

        recommendations = enhanced_result.get("enhanced_recommendations", [])
        print("\n📋 ENHANCED RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"   {i}. {rec}")

        print("\n📊 COGNITIVE ENHANCEMENT METRICS:")
        print(
            f"   Plugins Used: {len(enhanced_result.get('cognitive_pipeline_used', []))}"
        )
        print(f"   Analysis Depth: {len(str(enhanced_result))} characters")
        print(
            f"   Enhancement Applied: {'YES' if enhanced_result.get('cognitive_enhancement_applied') else 'NO'}"
        )

    else:
        print("❌ Cognitive enhancement failed")
        error = enhanced_result.get("enhancement_error", "Unknown error")
        print(f"Error: {error}")

    return enhanced_result


def compare_standard_vs_enhanced():
    """Show the difference between standard and enhanced approaches"""

    print("\n" + "=" * 60)
    print("📊 STANDARD vs ENHANCED COMPARISON")
    print("=" * 60)

    # Standard approach (what control agent would do)
    print("🔍 STANDARD APPROACH:")
    standard_recommendation = """
    1. Analyze current performance bottlenecks
    2. Evaluate budget constraints ($50K limit)
    3. Consider timeline pressures (3 months)
    4. Compare three options systematically
    5. Recommend based on risk/reward analysis
    
    RECOMMENDATION: Lean towards optimization due to timeline constraints
    """
    print(standard_recommendation)

    # Enhanced approach
    print("\n🚀 ENHANCED APPROACH (with cognitive pipeline):")
    enhanced_result = test_scenario_for_fresh_agent()

    # Show the difference
    print("\n📈 ENHANCEMENT VALUE:")
    if enhanced_result.get("cognitive_enhancement_applied"):
        print("✅ 4-plugin cognitive coordination")
        print("✅ Structured problem pre-analysis")
        print("✅ AI-powered reasoning and insights")
        print("✅ Workflow optimization recommendations")
        print("✅ Quality critique and improvement suggestions")
        print("✅ Comprehensive multi-dimensional analysis")
    else:
        print("❌ Enhancement failed - using standard approach")


if __name__ == "__main__":
    print("This scenario will be used to test fresh agents:")
    print("1. Fresh agent with cognitive enhancement (this script)")
    print("2. Control agent without enhancement (standard analysis)")
    print("3. Compare results for cognitive enhancement validation")

    compare_standard_vs_enhanced()
