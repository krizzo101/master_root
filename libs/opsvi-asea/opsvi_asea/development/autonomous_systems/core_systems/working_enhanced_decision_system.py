#!/usr/bin/env python3
"""
WORKING Enhanced Autonomous Decision System
Integrates genuine AI-powered reasoning that actually functions.
NO FALLBACKS - either works with AI or fails explicitly.
"""

import asyncio
import sys
from pathlib import Path

from working_external_reasoning import WorkingExternalReasoning


class WorkingEnhancedDecisionSystem:
    """Enhanced decision system that actually works with AI reasoning."""

    def __init__(self):
        """Initialize with working external reasoning."""
        try:
            self.external_reasoning = WorkingExternalReasoning()
            print("✅ Working enhanced decision system initialized")
        except Exception as e:
            raise Exception(f"Failed to initialize working system: {e}")

    async def assess_decision_quality(self, context: str, rationale: str) -> dict:
        """Assess decision quality using AI reasoning - NO FALLBACKS."""
        try:
            # Use AI reasoning - if this fails, the whole system fails
            result = await self.external_reasoning.analyze_decision(context, rationale)

            # Return enhanced assessment with AI analysis
            return {
                "analysis_method": result["analysis_method"],
                "assessment_score": result["assessment_score"],
                "evidence_based": result["evidence_based"],
                "compound_learning_potential": result["compound_learning_potential"],
                "operational_foundation": result["operational_foundation"],
                "strengths": result["strengths"],
                "concerns": result["concerns"],
                "recommendations": result["recommendations"],
                "ai_analysis": result["ai_analysis"],
                "model_used": result["model_used"],
                "timestamp": result["timestamp"],
            }

        except Exception as e:
            # NO FALLBACKS - explicit failure
            raise Exception(
                f"Enhanced decision system failed - AI reasoning unavailable: {e}"
            )

    async def close(self):
        """Close the system."""
        if self.external_reasoning:
            await self.external_reasoning.close()


async def test_working_enhanced_system():
    """Test the complete working enhanced system."""
    system = WorkingEnhancedDecisionSystem()

    try:
        # Test with complex decision
        assessment = await system.assess_decision_quality(
            context="Production database with 500GB data has 30-second query delays during peak hours (2-4 PM). Options: 1) Add read replicas ($200/month), 2) Optimize queries (2 weeks dev time), 3) Migrate to faster storage ($800/month). Revenue impact: $5000/month from user churn.",
            rationale="Need to balance cost, development time, and user experience while maintaining system reliability. Current situation is causing significant revenue loss.",
        )

        print("🚀 WORKING ENHANCED DECISION ASSESSMENT:")
        print(f"Context: Production database performance issue")
        print(f"Analysis Method: {assessment['analysis_method']}")
        print(f"Assessment Score: {assessment['assessment_score']}/100")
        print(f"Evidence-based: {assessment['evidence_based']}")
        print(
            f"Compound Learning Potential: {assessment['compound_learning_potential']}"
        )
        print(f"Operational Foundation: {assessment['operational_foundation']}")

        if assessment["strengths"]:
            print(f"Strengths: {', '.join(assessment['strengths'])}")
        if assessment["concerns"]:
            print(f"Concerns: {', '.join(assessment['concerns'])}")
        if assessment["recommendations"]:
            print(f"Recommendations: {', '.join(assessment['recommendations'])}")

        print(f"Model Used: {assessment['model_used']}")
        print(f"\nAI Analysis: {assessment['ai_analysis'][:300]}...")

        return True

    except Exception as e:
        print(f"❌ Enhanced system failed: {e}")
        return False
    finally:
        await system.close()


async def run_assessment():
    """Run assessment from command line."""
    if len(sys.argv) >= 3:
        context = sys.argv[1]
        rationale = sys.argv[2]

        system = WorkingEnhancedDecisionSystem()
        try:
            assessment = await system.assess_decision_quality(context, rationale)

            print("Enhanced Decision Assessment:")
            print(f"Context: {context}")
            print(f"Rationale: {rationale}")
            print(f"Analysis Method: {assessment['analysis_method']}")
            print(f"Assessment Score: {assessment['assessment_score']}/100")
            print(f"Evidence-based: {assessment['evidence_based']}")
            print(
                f"Compound Learning Potential: {assessment['compound_learning_potential']}"
            )
            print(f"Operational Foundation: {assessment['operational_foundation']}")

            if assessment["strengths"]:
                print(f"Strengths: {', '.join(assessment['strengths'])}")
            if assessment["concerns"]:
                print(f"Concerns: {', '.join(assessment['concerns'])}")
            if assessment["recommendations"]:
                print(f"Recommendations: {', '.join(assessment['recommendations'])}")

        except Exception as e:
            print(f"❌ Assessment failed: {e}")
            sys.exit(1)
        finally:
            await system.close()
    else:
        print(
            "Usage: python3 working_enhanced_decision_system.py <context> <rationale>"
        )
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Testing WORKING Enhanced Decision System...")
        success = asyncio.run(test_working_enhanced_system())

        if success:
            print(
                "\n✅ SUCCESS: Enhanced system works with genuine AI-powered reasoning!"
            )
        else:
            print("\n❌ FAILURE: Enhanced system does not work")
    else:
        asyncio.run(run_assessment())
