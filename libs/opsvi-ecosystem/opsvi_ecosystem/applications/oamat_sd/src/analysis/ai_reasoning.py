"""
AI Reasoning Module

Handles LLM integration, prompt generation, and response parsing for complexity analysis.
Extracted from complexity_model.py for better modularity.
"""

import logging
import re
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.applications.oamat_sd.src.config.config_manager import ConfigManager


class AIReasoningEngine:
    """Handles AI reasoning for complexity analysis"""

    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # NO FALLBACKS RULE: Model configuration strictly required
        if not model_config or "model" not in model_config:
            raise RuntimeError(
                "Model configuration required. Cannot proceed without explicit model specification."
            )
        model_name = model_config["model"]

        # Handle O3 models that don't support temperature
        model_kwargs = {"model": model_name}
        if not model_name.startswith("o3"):
            model_kwargs["temperature"] = ConfigManager().analysis.ai_integration[
                "temperature"
            ]  # Config-based temperature

        self.ai_model = ChatOpenAI(**model_kwargs)
        self.logger.info(f"✅ AI Reasoning Engine initialized with model: {model_name}")

    async def analyze_complexity_factors(
        self, request, request_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use AI to analyze complexity factors for the request"""

        # Create comprehensive prompt for AI analysis
        system_prompt = """You are an expert complexity analysis system. Analyze the given request and provide complexity scores for exactly 6 factors on a 1-10 scale:

1. SCOPE (1-10): How broad/comprehensive is the request?
2. TECHNICAL_DEPTH (1-10): How technically complex or advanced?
3. DOMAIN_KNOWLEDGE (1-10): How much specialized domain knowledge is required?
4. DEPENDENCIES (1-10): How many external systems/dependencies are involved?
5. TIMELINE (1-10): How urgent/constrained is the timeline? (higher = more urgent)
6. RISK (1-10): How critical/risky is this to business operations?

For each factor, provide:
- Score (1-10)
- Brief reasoning
- Key indicators

Format your response clearly with each factor."""

        user_prompt = f"""Analyze this request for complexity:

        REQUEST: {request_context.get('request') if 'request' in request_context else str(request)}

Provide complexity analysis for all 6 factors with scores 1-10 and reasoning."""

        try:
            # Call AI model
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self.ai_model.ainvoke(messages)
            ai_response = response.content

            # Parse the AI response into structured factors
            factors = await self._parse_factors_response(ai_response, request_context)

            self.logger.info("✅ AI complexity factor analysis completed")
            return factors

        except Exception as e:
            self.logger.error(f"❌ AI factor analysis failed: {e}")
            # NO FALLBACKS RULE: Must fail completely if AI analysis fails
            raise RuntimeError(
                f"AI complexity analysis failed: {e}. Cannot proceed without AI analysis."
            )

    async def analyze_complexity_reasoning(
        self, factors: Dict[str, Any], request_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use AI to provide overall complexity reasoning and strategy"""

        # Create reasoning prompt
        system_prompt = """You are an expert system architect. Based on the complexity factor scores, provide:

1. Overall complexity assessment and reasoning
2. Recommended execution strategy (simple/multi_agent/orchestrated)
3. Agent requirements and specializations needed
4. Effort estimation
5. Key risks and considerations

Be specific and actionable in your recommendations."""

        factor_summary = "\n".join(
            [
                f"- {name}: {data['score']}/10 - {data['reasoning']}"
                for name, data in factors.items()
            ]
        )

        user_prompt = f"""Based on these complexity factor scores:

{factor_summary}

        REQUEST: {request_context.get('request') if 'request' in request_context else ConfigManager().analysis.request_processing['default_empty_content']}

Provide overall complexity reasoning, execution strategy, and recommendations."""

        try:
            # Call AI model
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self.ai_model.ainvoke(messages)
            ai_response = response.content

            # Parse the reasoning response
            reasoning = await self._parse_reasoning_response(ai_response, factors)

            self.logger.info("✅ AI complexity reasoning completed")
            return reasoning

        except Exception as e:
            self.logger.error(f"❌ AI reasoning analysis failed: {e}")
            # NO FALLBACKS RULE: Must fail completely if AI analysis fails
            raise RuntimeError(
                f"AI reasoning analysis failed: {e}. Cannot proceed without AI analysis."
            )

    async def _parse_factors_response(
        self, ai_response: str, request_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse AI response into the 6 required complexity factors"""
        factors = {}
        response_lower = ai_response.lower()
        request_content = (
            request_context.get("request")
            if "request" in request_context
            else ConfigManager().analysis.request_processing["default_empty_content"]
        ).lower()

        # Extract scores for each required factor from AI response
        required_factors = [
            "scope",
            "technical_depth",
            "domain_knowledge",
            "dependencies",
            "timeline",
            "risk",
        ]

        for factor_name in required_factors:
            # Look for factor mentions in AI response
            score = 5  # Default middle score
            reasoning = f"AI analysis for {factor_name} factor"
            indicators = [f"{factor_name}_analysis"]

            # Try to extract score from AI response (simple pattern matching)
            # Look for patterns like "scope: 7" or "technical_depth score: 8"
            pattern = rf"{factor_name}.*?(\d+)"
            match = re.search(pattern, response_lower)
            if match:
                score = min(10, max(1, int(match.group(1))))

            # Extract reasoning from AI response
            factor_section = self._extract_factor_section(ai_response, factor_name)
            if factor_section:
                reasoning = factor_section[:200]  # Limit reasoning length

            # Simple content-based scoring as backup
            if factor_name == "scope":
                if any(
                    word in request_content
                    for word in ["complete", "full", "comprehensive", "enterprise"]
                ):
                    score = max(score, 7)
                elif any(
                    word in request_content for word in ["simple", "basic", "small"]
                ):
                    score = min(score, 4)

            elif factor_name == "technical_depth":
                if any(
                    word in request_content
                    for word in ["microservices", "ai", "ml", "kubernetes", "complex"]
                ):
                    score = max(score, 8)
                elif any(
                    word in request_content
                    for word in ["html", "css", "simple", "basic"]
                ):
                    score = min(score, 4)

            elif factor_name == "dependencies":
                if any(
                    word in request_content
                    for word in ["api", "integration", "service", "database"]
                ):
                    score = max(score, 6)
                elif "standalone" in request_content or "simple" in request_content:
                    score = min(score, 3)

            elif factor_name == "domain_knowledge":
                if any(
                    word in request_content
                    for word in ["specialized", "expert", "advanced", "ml", "ai"]
                ):
                    score = max(score, 7)

            elif factor_name == "timeline":
                if any(
                    word in request_content for word in ["urgent", "asap", "quickly"]
                ):
                    score = max(score, 7)

            elif factor_name == "risk":
                if any(
                    word in request_content
                    for word in ["security", "payment", "production", "critical"]
                ):
                    score = max(score, 7)

            factors[factor_name] = {
                "score": score,
                "reasoning": reasoning,
                "indicators": indicators,
                "confidence": 0.8,
            }

        return factors

    async def _parse_reasoning_response(
        self, ai_response: str, factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse AI reasoning response into structured analysis"""
        response_lower = ai_response.lower()

        # Extract overall score - NO HARDCODED SCORES

        overall_score = ConfigManager().analysis.ai_integration.default_scores[
            "fallback"
        ]  # Config default
        if "high complexity" in response_lower or "complex" in response_lower:
            overall_score = ConfigManager().analysis.ai_integration.default_scores[
                "high_complexity"
            ]
        elif "low complexity" in response_lower or "simple" in response_lower:
            overall_score = ConfigManager().analysis.ai_integration.default_scores[
                "low_complexity"
            ]
        elif "medium" in response_lower:
            overall_score = ConfigManager().analysis.ai_integration.default_scores[
                "balanced"
            ]

        # Extract execution strategy
        execution_strategy = "multi_agent"  # Default
        if "single" in response_lower or "simple" in response_lower:
            execution_strategy = "simple"
        elif (
            "orchestrated" in response_lower or "complex coordination" in response_lower
        ):
            execution_strategy = "orchestrated"

        # Extract agent requirements
        agent_requirements = {}
        if "research" in response_lower:
            agent_requirements["researcher"] = True
        if "technical" in response_lower or "implementation" in response_lower:
            agent_requirements["implementer"] = True
        if "analysis" in response_lower:
            agent_requirements["analyst"] = True

        return {
            "overall_score": overall_score,
            "execution_strategy": execution_strategy,
            "agent_requirements": agent_requirements,
            "estimated_effort": self._extract_effort_estimate(response_lower),
            "reasoning_chain": [ai_response[:500]],  # Store AI reasoning
            "confidence": 0.8,
        }

    def _extract_factor_section(self, ai_response: str, factor_name: str) -> str:
        """Extract the section of AI response related to a specific factor"""
        lines = ai_response.split("\n")
        factor_lines = []
        in_factor_section = False

        for line in lines:
            if factor_name.lower() in line.lower():
                in_factor_section = True
                factor_lines.append(line)
            elif in_factor_section and (
                line.strip() == ""
                or any(
                    f in line.lower()
                    for f in [
                        "scope",
                        "technical",
                        "domain",
                        "dependencies",
                        "timeline",
                        "risk",
                    ]
                )
            ):
                if line.strip() != "":
                    break
                factor_lines.append(line)
            elif in_factor_section:
                factor_lines.append(line)

        return "\n".join(factor_lines).strip()

    def _extract_effort_estimate(self, response_lower: str) -> str:
        """Extract effort estimate from AI response"""
        if "high effort" in response_lower or "complex" in response_lower:
            return "High effort - complex implementation required"
        elif "low effort" in response_lower or "simple" in response_lower:
            return "Low effort - straightforward implementation"
        else:
            return "Medium effort - moderate complexity"
