#!/usr/bin/env python3
"""
External Reasoning Service - NO FALLBACKS VERSION

Provides genuine AI-powered decision analysis using OpenAI Responses API.
If AI reasoning fails, the system FAILS EXPLICITLY - no fallbacks to inferior behavior.

This service delivers actual value through AI-powered reasoning or fails completely.
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime

from openai import AsyncOpenAI
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from schemas.decision_analysis_schemas import ExternalReasoningAnalysis
from core_systems.knowledge_context_gatherer import KnowledgeContextGatherer
from core_systems.comprehensive_logging_config import get_logger


class ExternalReasoningService:
    """
    External AI reasoning service with NO FALLBACKS.
    Either provides genuine AI-powered analysis or fails explicitly.
    """

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("external_reasoning_service", log_level="DEBUG")
        self.log = self.logger.get_logger()

        # Initialize OpenAI client using working pattern from ResponsesAPIClient
        self.api_key = config["external_reasoning"]["openai_api_key"]
        self.client = AsyncOpenAI(api_key=self.api_key)

        # Initialize knowledge context gatherer
        self.knowledge_gatherer = KnowledgeContextGatherer(config["database"])

        # Cost tracking
        self.total_cost = 0.0
        self.request_count = 0

        # Model selection for reasoning tasks
        self.reasoning_model = "gpt-4o"  # Use actual working model

        self.log.info("External reasoning service initialized with NO FALLBACKS")

    async def analyze_decision(
        self, context: str, rationale: str, additional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze decision using genuine AI reasoning.
        FAILS EXPLICITLY if AI reasoning unavailable.

        Args:
            context: Decision context
            rationale: Decision rationale
            additional_context: Additional context data

        Returns:
            AI-powered decision analysis or raises exception
        """
        correlation_id = self.logger.start_operation(
            "analyze_decision_with_ai",
            {"context_length": len(context), "model": self.reasoning_model},
        )

        try:
            # Gather knowledge context
            knowledge_context = await self.knowledge_gatherer.gather_decision_context(
                context
            )

            # Prepare instructions for AI reasoning
            instructions = """You are an expert decision analyst with advanced reasoning capabilities.

Analyze the provided decision context and rationale using multi-dimensional evaluation:

1. EVIDENCE ASSESSMENT: Evaluate the strength and quality of evidence supporting the decision
2. FEASIBILITY ANALYSIS: Assess operational feasibility and resource requirements
3. STRATEGIC ALIGNMENT: Determine alignment with long-term objectives
4. COMPOUND LEARNING: Identify opportunities for compound learning effects
5. RISK/OPPORTUNITY: Evaluate potential risks and opportunities
6. REASONING VALIDATION: Validate the logical consistency of the reasoning
7. ALTERNATIVES: Identify alternative approaches worth considering

Provide detailed analysis with specific confidence scores (0-100) for each dimension.
Use the structured format specified in the schema."""

            # Prepare user input
            user_input = f"""
DECISION ANALYSIS REQUEST

Context: {context}

Rationale: {rationale}

Additional Context: {json.dumps(additional_context, indent=2)}

Knowledge Context: {json.dumps(knowledge_context, indent=2)}

Please provide comprehensive multi-dimensional analysis using the structured format.
"""

            # Make AI reasoning call using Responses API pattern
            response = await self.client.responses.create(
                model=self.reasoning_model,
                instructions=instructions,
                input=user_input,
                text_format={
                    "format": {
                        "type": "json_schema",
                        "name": "decision_analysis_response",
                        "strict": True,
                        "schema": ExternalReasoningAnalysis.model_json_schema(),
                    }
                },
            )

            # Parse and validate response
            try:
                parsed_json = json.loads(response.output_text)
                validated_response = DecisionAnalysisResponse.model_validate(
                    parsed_json
                )
            except Exception as e:
                self.log.error(f"AI response validation failed: {e}")
                raise Exception(
                    f"AI reasoning service failed - invalid response format: {e}"
                )

            # Track usage and cost
            self.request_count += 1
            if hasattr(response, "usage"):
                usage = response.usage
                cost = self._calculate_cost(usage.input_tokens, usage.output_tokens)
                self.total_cost += cost

                self.log.info(
                    f"AI reasoning successful - tokens: {usage.total_tokens}, cost: ${cost:.4f}"
                )

            # Return successful AI analysis
            result = {
                "analysis_method": "ai_powered_reasoning",
                "assessment_score": validated_response.overall_assessment_score,
                "evidence_based": True,
                "compound_learning_potential": validated_response.compound_learning.has_potential,
                "operational_foundation": validated_response.feasibility_analysis.operational_feasibility
                > 70,
                "ai_analysis": validated_response.model_dump(),
                "cost_info": {
                    "request_cost": cost if hasattr(response, "usage") else 0,
                    "total_cost": self.total_cost,
                    "request_count": self.request_count,
                },
            }

            self.logger.end_operation(
                correlation_id,
                success=True,
                result_context={"assessment_score": result["assessment_score"]},
            )

            return result

        except Exception as e:
            self.logger.log_error_with_context(
                e, {"context": context[:100]}, correlation_id
            )
            self.logger.end_operation(correlation_id, success=False)

            # EXPLICIT FAILURE - NO FALLBACKS
            raise Exception(
                f"External reasoning service failed: {e}. System cannot provide AI-powered analysis."
            )

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for GPT-4o model."""
        # GPT-4o pricing: $2.50 per 1M input tokens, $10.00 per 1M output tokens
        input_cost = (input_tokens / 1_000_000) * 2.50
        output_cost = (output_tokens / 1_000_000) * 10.00
        return input_cost + output_cost

    async def close(self):
        """Close connections."""
        if self.client:
            await self.client.close()
        if self.knowledge_gatherer:
            self.knowledge_gatherer.close()

        self.log.info(
            f"External reasoning service closed. Total cost: ${self.total_cost:.4f}"
        )


async def test_external_reasoning():
    """Test the external reasoning service."""
    import json

    # Load config
    with open(
        "/home/opsvi/asea/development/autonomous_systems/config/autonomous_systems_config.json",
        "r",
    ) as f:
        config = json.load(f)

    service = ExternalReasoningService(config)

    try:
        result = await service.analyze_decision(
            context="Test decision context for validation",
            rationale="Testing AI reasoning capabilities",
            additional_context={"test": True},
        )

        print("✅ External reasoning service working!")
        print(f"Analysis method: {result['analysis_method']}")
        print(f"Assessment score: {result['assessment_score']}")
        print(f"Evidence-based: {result['evidence_based']}")

    except Exception as e:
        print(f"❌ External reasoning service failed: {e}")
        raise
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(test_external_reasoning())
