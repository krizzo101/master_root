#!/usr/bin/env python3
"""
Autonomous Decision Analyst
Properly optimized for autonomous agent decision making analysis.
"""

import asyncio
import json
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from openai import AsyncOpenAI


class AutonomousDecisionAnalyst:
    """AI analyst specifically optimized for autonomous agent decision making."""

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

        print("🤖 Autonomous Decision Analyst Initialized")
        print("Optimized for AI agent autonomous execution analysis")

    def get_autonomous_system_prompt(self) -> str:
        """Get system prompt optimized for autonomous agent decision analysis."""
        return """You are an Autonomous Systems Decision Analyst. You analyze decisions that will be executed by AI agents WITHOUT human oversight.

CRITICAL CONTEXT:
- The EXECUTOR is an autonomous AI agent, not humans
- Execution happens WITHOUT human intervention or approval
- Decisions must be AUTONOMOUSLY EXECUTABLE using available tools
- Failures must be AUTONOMOUSLY DETECTABLE and RECOVERABLE
- Success must be PROGRAMMATICALLY VERIFIABLE

AVAILABLE AGENT CAPABILITIES:
- Database operations (ArangoDB queries, updates, inserts)
- File system operations (read, write, edit files)
- Shell command execution
- API calls (OpenAI, web requests)
- Code execution and testing
- Git operations
- Knowledge base management

AGENT LIMITATIONS:
- Cannot access external systems without API keys
- Cannot perform actions requiring human approval
- Cannot handle ambiguous success criteria
- Cannot recover from failures without programmatic detection
- Cannot access GUI applications or manual processes

ANALYSIS DIMENSIONS (0-100 scale):
1. Autonomous Executability: Can the AI agent execute this completely autonomously?
2. Tool Availability: Does the agent have all required tools and access?
3. Error Detection: Can execution failures be programmatically detected?
4. Recovery Capability: Can the agent recover from likely failure modes?
5. Validation Criteria: Can success be programmatically verified?
6. Cascading Risk: What's the autonomous failure impact?
7. Agent Learning: How does this advance autonomous capabilities?

RESPONSE FORMAT:
Provide specific scores (0-100) for each dimension with detailed reasoning focused on AUTONOMOUS EXECUTION CONSTRAINTS."""

    def get_autonomous_user_prompt(
        self, context: str, rationale: str, agent_capabilities: Dict[str, Any] = None
    ) -> str:
        """Get user prompt with autonomous execution context."""

        capabilities_text = ""
        if agent_capabilities:
            capabilities_text = (
                f"\nCURRENT AGENT STATE:\n{json.dumps(agent_capabilities, indent=2)}\n"
            )

        return f"""AUTONOMOUS DECISION ANALYSIS REQUEST

DECISION CONTEXT: {context}

DECISION RATIONALE: {rationale}
{capabilities_text}
ANALYSIS REQUIREMENT:
Analyze this decision for AUTONOMOUS AI AGENT EXECUTION. The agent will execute this decision without human oversight using available tools and capabilities.

Focus on:
- Can the agent actually execute this autonomously?
- What tools/resources are required and available?
- How will the agent detect success or failure?
- What happens if this goes wrong during autonomous execution?
- How does this advance the agent's autonomous capabilities?

Provide scores (0-100) for all 7 autonomous execution dimensions with specific reasoning."""

    async def analyze_autonomous_decision(
        self, context: str, rationale: str, agent_capabilities: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze decision for autonomous agent execution."""

        system_prompt = self.get_autonomous_system_prompt()
        user_prompt = self.get_autonomous_user_prompt(
            context, rationale, agent_capabilities
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=600,
                temperature=0.1,
            )

            ai_analysis = response.choices[0].message.content

            # Extract autonomous-specific scores
            scores = {
                "autonomous_executability": self._extract_score(
                    ai_analysis, "Autonomous Executability"
                ),
                "tool_availability": self._extract_score(
                    ai_analysis, "Tool Availability"
                ),
                "error_detection": self._extract_score(ai_analysis, "Error Detection"),
                "recovery_capability": self._extract_score(
                    ai_analysis, "Recovery Capability"
                ),
                "validation_criteria": self._extract_score(
                    ai_analysis, "Validation Criteria"
                ),
                "cascading_risk": self._extract_score(ai_analysis, "Cascading Risk"),
                "agent_learning": self._extract_score(ai_analysis, "Agent Learning"),
            }

            # Calculate autonomous execution readiness
            execution_readiness = int(
                (
                    scores["autonomous_executability"] * 0.25
                    + scores["tool_availability"] * 0.20
                    + scores["error_detection"] * 0.15
                    + scores["recovery_capability"] * 0.15
                    + scores["validation_criteria"] * 0.15
                    + (100 - scores["cascading_risk"])
                    * 0.10  # Lower risk = higher readiness
                )
            )

            # Determine autonomous execution recommendation
            if execution_readiness >= 80:
                recommendation = "EXECUTE_AUTONOMOUSLY"
            elif execution_readiness >= 60:
                recommendation = "EXECUTE_WITH_MONITORING"
            elif execution_readiness >= 40:
                recommendation = "REQUIRES_ENHANCEMENT"
            else:
                recommendation = "NOT_AUTONOMOUS_READY"

            return {
                "analysis_method": "autonomous_agent_optimized",
                "execution_readiness": execution_readiness,
                "autonomous_recommendation": recommendation,
                "scores": scores,
                "autonomous_executable": scores["autonomous_executability"] >= 70,
                "tools_available": scores["tool_availability"] >= 70,
                "error_recoverable": scores["error_detection"] >= 60
                and scores["recovery_capability"] >= 60,
                "success_verifiable": scores["validation_criteria"] >= 70,
                "low_cascading_risk": scores["cascading_risk"] <= 40,
                "advances_capabilities": scores["agent_learning"] >= 60,
                "ai_analysis": ai_analysis,
                "autonomous_constraints": self._extract_constraints(ai_analysis),
                "execution_requirements": self._extract_requirements(ai_analysis),
                "failure_modes": self._extract_failure_modes(ai_analysis),
                "success_criteria": self._extract_success_criteria(ai_analysis),
                "model_used": self.model,
                "timestamp": datetime.now().isoformat(),
                "token_usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        except Exception as e:
            raise Exception(f"Autonomous decision analysis failed: {e}")

    def _extract_score(self, text: str, dimension: str) -> int:
        """Extract score for specific autonomous dimension."""
        import re

        # More specific patterns for autonomous dimensions
        patterns = [
            rf"{dimension}[^:]*:\s*(\d+)",
            rf"{dimension}[^:]*:\s*(\d+)/100",
            rf"{dimension}[^:]*:\s*(\d+)%",
            rf"(\d+)/100.*{dimension}",
            rf"(\d+).*{dimension}",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        # Default based on dimension type
        defaults = {
            "Autonomous Executability": 50,
            "Tool Availability": 70,
            "Error Detection": 60,
            "Recovery Capability": 50,
            "Validation Criteria": 60,
            "Cascading Risk": 50,
            "Agent Learning": 60,
        }
        return defaults.get(dimension, 50)

    def _extract_constraints(self, text: str) -> list:
        """Extract autonomous execution constraints."""
        constraints = []
        constraint_keywords = [
            ("requires human", "Human intervention required"),
            ("manual", "Manual process required"),
            ("gui", "GUI interaction required"),
            ("approval", "Human approval required"),
            ("ambiguous", "Ambiguous success criteria"),
            ("external system", "External system dependency"),
            ("credentials", "Missing credentials/access"),
        ]

        for keyword, constraint in constraint_keywords:
            if keyword in text.lower():
                constraints.append(constraint)

        return constraints

    def _extract_requirements(self, text: str) -> list:
        """Extract autonomous execution requirements."""
        requirements = []
        requirement_keywords = [
            ("database", "Database access required"),
            ("api", "API access required"),
            ("file", "File system access required"),
            ("shell", "Shell command execution required"),
            ("git", "Git operations required"),
            ("monitoring", "Monitoring capability required"),
            ("validation", "Validation system required"),
        ]

        for keyword, requirement in requirement_keywords:
            if keyword in text.lower():
                requirements.append(requirement)

        return requirements

    def _extract_failure_modes(self, text: str) -> list:
        """Extract autonomous failure modes."""
        failure_modes = []
        failure_keywords = [
            ("timeout", "Operation timeout"),
            ("connection", "Connection failure"),
            ("permission", "Permission denied"),
            ("resource", "Resource unavailable"),
            ("syntax", "Syntax error"),
            ("validation", "Validation failure"),
            ("cascade", "Cascading failure"),
        ]

        for keyword, failure in failure_keywords:
            if keyword in text.lower():
                failure_modes.append(failure)

        return failure_modes

    def _extract_success_criteria(self, text: str) -> list:
        """Extract success criteria."""
        criteria = []
        criteria_keywords = [
            ("status code", "HTTP status validation"),
            ("database", "Database state validation"),
            ("file exists", "File existence validation"),
            ("response", "Response validation"),
            ("metric", "Metric validation"),
            ("log", "Log validation"),
            ("test", "Test execution validation"),
        ]

        for keyword, criterion in criteria_keywords:
            if keyword in text.lower():
                criteria.append(criterion)

        return criteria

    async def close(self):
        """Close the client."""
        if self.client:
            await self.client.close()


async def demonstrate_autonomous_analysis():
    """Demonstrate autonomous-optimized decision analysis."""
    analyst = AutonomousDecisionAnalyst()

    try:
        print("🎯 AUTONOMOUS DECISION ANALYSIS DEMONSTRATION")
        print("=" * 60)

        # Test with autonomous execution context
        context = "Database query optimization: Slow queries identified in agent_memory collection. Options: 1) Create indexes on frequently queried fields, 2) Implement query result caching, 3) Optimize AQL query patterns in existing code."

        rationale = "Agent performance is degraded due to slow database queries during autonomous operations. Need solution that can be implemented and validated autonomously without human intervention."

        agent_capabilities = {
            "database_access": True,
            "arangodb_admin": True,
            "code_modification": True,
            "testing_framework": True,
            "monitoring_tools": True,
            "git_operations": True,
        }

        print(f"CONTEXT: {context}")
        print(f"RATIONALE: {rationale}")
        print(f"AGENT CAPABILITIES: {json.dumps(agent_capabilities, indent=2)}")
        print()

        result = await analyst.analyze_autonomous_decision(
            context, rationale, agent_capabilities
        )

        print("🤖 AUTONOMOUS EXECUTION ANALYSIS:")
        print("=" * 40)
        print(f"Execution Readiness: {result['execution_readiness']}/100")
        print(f"Recommendation: {result['autonomous_recommendation']}")
        print(f"Autonomous Executable: {result['autonomous_executable']}")
        print(f"Tools Available: {result['tools_available']}")
        print(f"Error Recoverable: {result['error_recoverable']}")
        print(f"Success Verifiable: {result['success_verifiable']}")
        print(f"Low Cascading Risk: {result['low_cascading_risk']}")
        print(f"Advances Capabilities: {result['advances_capabilities']}")
        print()

        print("📊 AUTONOMOUS DIMENSION SCORES:")
        print("=" * 40)
        for dimension, score in result["scores"].items():
            print(f"{dimension.replace('_', ' ').title()}: {score}/100")
        print()

        if result["autonomous_constraints"]:
            print(f"⚠️ Constraints: {', '.join(result['autonomous_constraints'])}")
        if result["execution_requirements"]:
            print(f"🔧 Requirements: {', '.join(result['execution_requirements'])}")
        if result["failure_modes"]:
            print(f"💥 Failure Modes: {', '.join(result['failure_modes'])}")
        if result["success_criteria"]:
            print(f"✅ Success Criteria: {', '.join(result['success_criteria'])}")

        print("\n📝 AI ANALYSIS PREVIEW:")
        print("=" * 40)
        print(result["ai_analysis"][:300] + "...")

        return result

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None
    finally:
        await analyst.close()


if __name__ == "__main__":
    asyncio.run(demonstrate_autonomous_analysis())
