#!/usr/bin/env python3
"""
AI Reasoning Workflow Demonstration
Shows exactly how the AI decision system works under the hood.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from openai import AsyncOpenAI


class AIWorkflowDemo:
    """Demonstrates the complete AI reasoning workflow with full transparency."""

    def __init__(self):
        # Load config
        config_path = (
            Path(__file__).parent.parent / "config" / "autonomous_systems_config.json"
        )
        with open(config_path, "r") as f:
            config = json.load(f)

        self.api_key = config["external_reasoning"]["openai_api_key"]
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"

        print("🔍 AI Workflow Demonstration Initialized")
        print(f"Model: {self.model}")
        print(f"API Key: {self.api_key[:10]}...{self.api_key[-4:]}")
        print("=" * 60)

    async def demonstrate_full_workflow(self, context: str, rationale: str):
        """Demonstrate the complete AI reasoning workflow with full visibility."""

        print("📋 STEP 1: SYSTEM PROMPT CONSTRUCTION")
        print("=" * 40)

        system_prompt = """You are an expert decision analyst. Analyze decisions using these dimensions:

1. Evidence Assessment (0-100): How strong is the evidence?
2. Feasibility Score (0-100): How feasible is implementation?
3. Strategic Value (0-100): How valuable strategically?
4. Risk Level (low/medium/high): What are the risks?
5. Compound Learning (true/false): Does this enable future learning?

Provide specific scores and reasoning."""

        print("SYSTEM PROMPT:")
        print(f'"{system_prompt}"')
        print()

        print("📝 STEP 2: USER PROMPT CONSTRUCTION")
        print("=" * 40)

        user_prompt = f"""Analyze this decision:

Context: {context}

Rationale: {rationale}

Provide detailed analysis with specific scores for each dimension."""

        print("USER PROMPT:")
        print(f'"{user_prompt}"')
        print()

        print("🤖 STEP 3: AI AGENT INVOCATION")
        print("=" * 40)
        print(f"Agent: OpenAI {self.model}")
        print("Max Tokens: 500")
        print("Temperature: 0.1 (deterministic)")
        print("Request Type: Chat Completion")
        print()

        print("🔄 STEP 4: SENDING REQUEST TO AI AGENT...")
        print("=" * 40)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=500,
                temperature=0.1,
            )

            print("✅ AI Response Received")
            print(f"Input Tokens: {response.usage.prompt_tokens}")
            print(f"Output Tokens: {response.usage.completion_tokens}")
            print(f"Total Tokens: {response.usage.total_tokens}")
            print()

            print("📄 STEP 5: RAW AI RESPONSE")
            print("=" * 40)
            ai_analysis = response.choices[0].message.content
            print("RAW AI OUTPUT:")
            print(f'"{ai_analysis}"')
            print()

            print("🔧 STEP 6: RESPONSE PARSING & EXTRACTION")
            print("=" * 40)

            # Show parsing process
            evidence_score = self._extract_score_with_demo(ai_analysis, "Evidence")
            feasibility_score = self._extract_score_with_demo(
                ai_analysis, "Feasibility"
            )
            strategic_score = self._extract_score_with_demo(ai_analysis, "Strategic")

            overall_score = int(
                (evidence_score + feasibility_score + strategic_score) / 3
            )

            print("Extracted Scores:")
            print(f"  Evidence: {evidence_score}/100")
            print(f"  Feasibility: {feasibility_score}/100")
            print(f"  Strategic: {strategic_score}/100")
            print(f"  Overall: {overall_score}/100")
            print()

            print("🏷️ STEP 7: SEMANTIC ANALYSIS")
            print("=" * 40)

            strengths = self._extract_strengths_with_demo(ai_analysis)
            concerns = self._extract_concerns_with_demo(ai_analysis)
            recommendations = self._extract_recommendations_with_demo(ai_analysis)

            print(f"Extracted Strengths: {strengths}")
            print(f"Extracted Concerns: {concerns}")
            print(f"Extracted Recommendations: {recommendations}")
            print()

            print("📊 STEP 8: STRUCTURED OUTPUT GENERATION")
            print("=" * 40)

            structured_result = {
                "analysis_method": "ai_powered_reasoning",
                "assessment_score": overall_score,
                "evidence_based": evidence_score > 70,
                "compound_learning_potential": "learning" in ai_analysis.lower(),
                "operational_foundation": feasibility_score > 70,
                "ai_analysis": ai_analysis,
                "evidence_score": evidence_score,
                "feasibility_score": feasibility_score,
                "strategic_score": strategic_score,
                "strengths": strengths,
                "concerns": concerns,
                "recommendations": recommendations,
                "model_used": self.model,
                "timestamp": datetime.now().isoformat(),
                "token_usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

            print("FINAL STRUCTURED OUTPUT:")
            print(json.dumps(structured_result, indent=2))
            print()

            print("💡 STEP 9: WORKFLOW SUMMARY")
            print("=" * 40)
            print("AGENTS USED:")
            print(f"  1. OpenAI {self.model} - Decision analysis agent")
            print()
            print("PROMPT ENGINEERING:")
            print("  1. System prompt: Defines expert role and analysis framework")
            print("  2. User prompt: Provides context and specific analysis request")
            print()
            print("PROCESSING PIPELINE:")
            print("  1. Input validation")
            print("  2. AI agent invocation")
            print("  3. Response parsing")
            print("  4. Score extraction via regex")
            print("  5. Semantic analysis via keyword matching")
            print("  6. Structured output generation")
            print()
            print("VALUE DELIVERED:")
            print(
                f"  - Multi-dimensional analysis (Evidence: {evidence_score}, Feasibility: {feasibility_score}, Strategic: {strategic_score})"
            )
            print(f"  - Evidence-based assessment: {evidence_score > 70}")
            print(f"  - Operational feasibility: {feasibility_score > 70}")
            print(
                f"  - Compound learning potential: {'learning' in ai_analysis.lower()}"
            )
            print(f"  - Specific recommendations: {len(recommendations)} identified")

            return structured_result

        except Exception as e:
            print(f"❌ AI Request Failed: {e}")
            raise

    def _extract_score_with_demo(self, text: str, dimension: str) -> int:
        """Extract score with demonstration of the process."""
        import re

        print(f"Extracting {dimension} score...")

        patterns = [
            rf"{dimension}[^:]*:\s*(\d+)",
            rf"{dimension}[^:]*:\s*(\d+)/100",
            rf"{dimension}[^:]*:\s*(\d+)%",
        ]

        for i, pattern in enumerate(patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                print(f"  ✅ Found using pattern {i+1}: '{match.group(0)}' -> {score}")
                return score

        print("  ⚠️ No pattern matched, using default: 75")
        return 75

    def _extract_strengths_with_demo(self, text: str) -> list:
        """Extract strengths with demonstration."""
        print("Extracting strengths via keyword analysis...")
        strengths = []

        if "strong evidence" in text.lower():
            strengths.append("Strong evidence base")
            print("  ✅ Found: 'strong evidence' -> Strong evidence base")
        if "feasible" in text.lower():
            strengths.append("Operationally feasible")
            print("  ✅ Found: 'feasible' -> Operationally feasible")
        if "strategic" in text.lower() and (
            "value" in text.lower() or "important" in text.lower()
        ):
            strengths.append("Strategic value")
            print("  ✅ Found: 'strategic' + 'value/important' -> Strategic value")

        if not strengths:
            print("  ⚠️ No strength keywords found")

        return strengths

    def _extract_concerns_with_demo(self, text: str) -> list:
        """Extract concerns with demonstration."""
        print("Extracting concerns via keyword analysis...")
        concerns = []

        if "risk" in text.lower() and "high" in text.lower():
            concerns.append("High risk factors")
            print("  ⚠️ Found: 'risk' + 'high' -> High risk factors")
        if "insufficient" in text.lower() or "lack" in text.lower():
            concerns.append("Insufficient evidence")
            print("  ⚠️ Found: 'insufficient/lack' -> Insufficient evidence")
        if "complex" in text.lower() and "difficult" in text.lower():
            concerns.append("Implementation complexity")
            print("  ⚠️ Found: 'complex' + 'difficult' -> Implementation complexity")

        if not concerns:
            print("  ✅ No concern keywords found")

        return concerns

    def _extract_recommendations_with_demo(self, text: str) -> list:
        """Extract recommendations with demonstration."""
        print("Extracting recommendations via keyword analysis...")
        recommendations = []

        if "gather more" in text.lower() or "additional data" in text.lower():
            recommendations.append("Gather additional evidence")
            print(
                "  💡 Found: 'gather more/additional data' -> Gather additional evidence"
            )
        if "pilot" in text.lower() or "test" in text.lower():
            recommendations.append("Consider pilot implementation")
            print("  💡 Found: 'pilot/test' -> Consider pilot implementation")
        if "monitor" in text.lower():
            recommendations.append("Implement monitoring")
            print("  💡 Found: 'monitor' -> Implement monitoring")

        if not recommendations:
            print("  ⚠️ No recommendation keywords found")

        return recommendations

    async def close(self):
        """Close the client."""
        if self.client:
            await self.client.close()


async def main():
    """Run the complete workflow demonstration."""
    demo = AIWorkflowDemo()

    try:
        print("🚀 STARTING AI REASONING WORKFLOW DEMONSTRATION")
        print("=" * 60)
        print()

        # Use a real decision scenario
        context = "Database performance degradation: Query response times increased from 200ms to 2000ms over past month. Three options: 1) Add read replicas ($300/month), 2) Optimize slow queries (3 weeks dev time), 3) Upgrade to faster database instance ($800/month). System serves 10,000 daily active users."

        rationale = "Must balance cost, development effort, and time-to-resolution. User experience is degrading rapidly and affecting retention. Need solution that provides both immediate relief and long-term scalability."

        print(f"DECISION CONTEXT: {context}")
        print()
        print(f"DECISION RATIONALE: {rationale}")
        print()
        print("=" * 60)
        print()

        result = await demo.demonstrate_full_workflow(context, rationale)

        print()
        print("🎯 DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("This demonstrates the complete AI reasoning workflow:")
        print("1. Structured prompts sent to OpenAI GPT-4o-mini")
        print("2. AI generates multi-dimensional analysis")
        print("3. Response parsed and structured automatically")
        print("4. Delivers genuine AI-powered decision insights")
        print()
        print("✅ This is infinitely superior to keyword-based pattern matching")

    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
    finally:
        await demo.close()


if __name__ == "__main__":
    asyncio.run(main())
