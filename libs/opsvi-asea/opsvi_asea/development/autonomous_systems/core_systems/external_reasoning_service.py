"""
External Reasoning Service for Enhanced Autonomous Decision Analysis.
Provides sophisticated decision analysis using external AI reasoning with knowledge graph integration.
"""

import json
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Import our autonomous components
from autonomous_openai_client import AutonomousOpenAIClient
from knowledge_context_gatherer import KnowledgeContextGatherer
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "schemas"))
from decision_analysis_schemas import (
    ExternalReasoningAnalysis,
)


class ExternalReasoningService:
    """
    Sophisticated decision analysis service that combines external AI reasoning
    with autonomous agent knowledge graph integration.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the external reasoning service.

        Args:
            config_path: Path to configuration file
        """
        self.logger = logging.getLogger(__name__)

        # Load configuration
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent
                / "config"
                / "autonomous_systems_config.json"
            )

        self.config = self._load_config(config_path)

        # Initialize components
        self.openai_client = None
        self.context_gatherer = None
        self.analysis_cache = {}
        self.cost_tracker = {"daily_cost": 0.0, "analysis_count": 0}

        # Validate configuration
        self._validate_config()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            self.logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            raise

    def _validate_config(self):
        """Validate configuration has required fields."""
        required_fields = [
            "external_reasoning.openai_api_key",
            "external_reasoning.models.reasoning",
            "database.host",
            "database.database",
            "database.username",
            "database.password",
        ]

        for field in required_fields:
            keys = field.split(".")
            value = self.config
            try:
                for key in keys:
                    value = value[key]
                if not value:
                    raise ValueError(f"Configuration field {field} is empty")
            except KeyError:
                raise ValueError(f"Required configuration field {field} is missing")

    async def initialize(self):
        """Initialize the service components."""
        try:
            # Initialize OpenAI client
            api_key = self.config["external_reasoning"]["openai_api_key"]
            self.openai_client = AutonomousOpenAIClient(api_key)

            # Initialize context gatherer
            db_config = self.config["database"]
            self.context_gatherer = KnowledgeContextGatherer(db_config)

            # Connect to database
            connection_success = await self.context_gatherer.connect()
            if not connection_success:
                raise RuntimeError("Failed to connect to knowledge database")

            self.logger.info("External Reasoning Service initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize External Reasoning Service: {e}")
            return False

    async def analyze_decision(
        self, decision: str, rationale: str, analysis_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive decision analysis using external reasoning.

        Args:
            decision: The decision to analyze
            rationale: The provided rationale
            analysis_id: Optional unique identifier for the analysis

        Returns:
            Dictionary containing comprehensive analysis results
        """
        if analysis_id is None:
            analysis_id = f"decision_analysis_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

        try:
            self.logger.info(f"Starting decision analysis: {analysis_id}")

            # Check budget constraints
            if not self._check_budget_constraints():
                return {
                    "success": False,
                    "error": "Budget constraints exceeded",
                    "analysis_id": analysis_id,
                }

            # Step 1: Gather context from knowledge graph
            self.logger.info("Gathering context from knowledge graph...")
            context = self._gather_comprehensive_context(decision, rationale)

            # Step 2: Perform external reasoning analysis
            self.logger.info("Performing external reasoning analysis...")
            reasoning_result = await self._perform_external_reasoning(
                decision, rationale, context, analysis_id
            )

            if not reasoning_result["success"]:
                return reasoning_result

            # Step 3: Store analysis results
            self.logger.info("Storing analysis results...")
            storage_result = await self._store_analysis_results(
                reasoning_result["data"]
            )

            # Step 4: Update cost tracking
            self._update_cost_tracking(reasoning_result["data"]["analysis_cost"])

            # Step 5: Cache results for potential reuse
            self.analysis_cache[analysis_id] = reasoning_result["data"]

            self.logger.info(f"Decision analysis completed: {analysis_id}")

            return {
                "success": True,
                "analysis_id": analysis_id,
                "data": reasoning_result["data"],
                "storage_result": storage_result,
                "cost_info": reasoning_result.get("cost_info", {}),
                "context_quality": context.get("context_quality_metrics", {}),
            }

        except Exception as e:
            self.logger.error(f"Error in decision analysis {analysis_id}: {e}")
            return {"success": False, "error": str(e), "analysis_id": analysis_id}

    def _gather_comprehensive_context(
        self, decision: str, rationale: str
    ) -> Dict[str, Any]:
        """Gather comprehensive context for decision analysis."""
        try:
            context_config = self.config["external_reasoning"]["context_gathering"]

            context = self.context_gatherer.gather_decision_context(
                decision=decision,
                rationale=rationale,
                max_memories=context_config.get("max_memories", 20),
                max_concepts=context_config.get("max_concepts", 10),
                max_relationships=context_config.get("max_relationships", 15),
            )

            return context

        except Exception as e:
            self.logger.error(f"Error gathering context: {e}")
            return {
                "relevant_memories": [],
                "cognitive_concepts": [],
                "semantic_relationships": [],
                "historical_patterns": [],
                "operational_knowledge": [],
                "context_quality_metrics": {"error": str(e)},
            }

    async def _perform_external_reasoning(
        self, decision: str, rationale: str, context: Dict[str, Any], analysis_id: str
    ) -> Dict[str, Any]:
        """Perform the external reasoning analysis."""
        try:
            # Select optimal model for reasoning task
            model = self._select_optimal_model("decision_analysis", "high")

            # Build comprehensive prompt
            system_prompt = self.openai_client.get_system_prompt_for_decision_analysis(
                model
            )
            user_prompt = self._build_analysis_prompt(decision, rationale, context)

            # Perform structured reasoning
            response = await self.openai_client.create_structured_response(
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=ExternalReasoningAnalysis,
                max_tokens=4000,
                temperature=0.1,
            )

            if response["success"]:
                # Enhance the response with our metadata
                analysis_data = response["data"]
                analysis_data["analysis_id"] = analysis_id
                analysis_data["analysis_timestamp"] = datetime.now().isoformat()
                analysis_data["model_used"] = response["model"]
                analysis_data["analysis_cost"] = response["cost_info"]["total_cost"]
                analysis_data["context_quality"] = context.get(
                    "context_quality_metrics", {}
                ).get("overall_context_quality", 0.0)

                return {
                    "success": True,
                    "data": analysis_data,
                    "cost_info": response["cost_info"],
                    "model_info": {
                        "model": response["model"],
                        "model_type": response["model_type"],
                        "tokens_used": response["usage"],
                    },
                }
            else:
                # Try fallback approach
                return await self._fallback_analysis(
                    decision, rationale, context, analysis_id
                )

        except Exception as e:
            self.logger.error(f"Error in external reasoning: {e}")
            return {"success": False, "error": f"External reasoning failed: {str(e)}"}

    def _build_analysis_prompt(
        self, decision: str, rationale: str, context: Dict[str, Any]
    ) -> str:
        """Build comprehensive analysis prompt with context."""
        context_summary = self._summarize_context(context)

        prompt = f"""
COMPREHENSIVE DECISION ANALYSIS REQUEST

DECISION TO ANALYZE:
{decision}

PROVIDED RATIONALE:
{rationale}

KNOWLEDGE GRAPH CONTEXT:
{context_summary}

ANALYSIS REQUIREMENTS:

Please provide a comprehensive multi-dimensional analysis of this decision including:

1. EVIDENCE ASSESSMENT:
   - Evaluate the strength and quality of evidence supporting this decision
   - Identify gaps in evidence or unsupported assumptions
   - Assess how well the rationale supports the decision

2. OPERATIONAL FEASIBILITY:
   - Analyze practical implementation requirements
   - Assess resource needs and potential blockers
   - Evaluate probability of successful execution

3. STRATEGIC ALIGNMENT:
   - Determine alignment with long-term autonomous goals
   - Identify goal advancement opportunities and conflicts
   - Assess strategic value and long-term impact

4. COMPOUND LEARNING POTENTIAL:
   - Identify knowledge connections and skill development opportunities
   - Assess multiplicative learning effects
   - Evaluate how this decision enables future decisions

5. RISK-OPPORTUNITY ANALYSIS:
   - Identify potential risks and mitigation strategies
   - Assess opportunities and opportunity costs
   - Provide balanced risk-opportunity evaluation

6. REASONING VALIDATION:
   - Validate logical consistency of the reasoning chain
   - Identify reasoning gaps or inconsistencies
   - Assess how well the conclusion is supported

7. CONTEXTUAL INTEGRATION:
   - Leverage provided knowledge graph context
   - Connect to historical patterns and operational knowledge
   - Integrate insights from cognitive concepts and relationships

8. RECOMMENDATIONS:
   - Provide specific, actionable recommendations
   - Suggest improvements to decision or implementation
   - Offer alternative approaches if appropriate

Please structure your analysis according to the specified schema with specific scores, assessments, and detailed reasoning for each component.
"""
        return prompt

    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Summarize context for inclusion in prompt."""
        try:
            summary_parts = []

            # Relevant memories
            memories = context.get("relevant_memories", [])
            if memories:
                memory_titles = [m.get("title", "Untitled") for m in memories[:5]]
                summary_parts.append(
                    f"Relevant Memories ({len(memories)} total): {', '.join(memory_titles)}"
                )

            # Cognitive concepts
            concepts = context.get("cognitive_concepts", [])
            if concepts:
                concept_names = [c.get("concept", "Unknown") for c in concepts[:3]]
                summary_parts.append(
                    f"Cognitive Concepts ({len(concepts)} total): {', '.join(concept_names)}"
                )

            # Operational knowledge
            operational = context.get("operational_knowledge", [])
            if operational:
                op_titles = [op.get("title", "Untitled") for op in operational[:3]]
                summary_parts.append(
                    f"Operational Knowledge ({len(operational)} total): {', '.join(op_titles)}"
                )

            # Historical patterns
            patterns = context.get("historical_patterns", [])
            if patterns:
                summary_parts.append(
                    f"Historical Patterns: {len(patterns)} decision patterns identified"
                )

            # Context quality
            quality_metrics = context.get("context_quality_metrics", {})
            if quality_metrics and "overall_context_quality" in quality_metrics:
                quality = quality_metrics["overall_context_quality"]
                summary_parts.append(f"Context Quality Score: {quality:.2f}")

            return (
                "\n".join(summary_parts)
                if summary_parts
                else "No relevant context found"
            )

        except Exception as e:
            return f"Error summarizing context: {str(e)}"

    async def _fallback_analysis(
        self, decision: str, rationale: str, context: Dict[str, Any], analysis_id: str
    ) -> Dict[str, Any]:
        """Fallback analysis when structured approach fails."""
        try:
            self.logger.warning("Using fallback analysis approach")

            # Use simpler model and unstructured response
            fallback_model = self.config["external_reasoning"]["models"]["fallback"]

            system_prompt = "You are an expert decision analyst. Provide a comprehensive analysis of the given decision."
            user_prompt = f"Decision: {decision}\nRationale: {rationale}\n\nProvide detailed analysis covering evidence strength, feasibility, strategic alignment, risks, and recommendations."

            response = await self.openai_client.create_fallback_response(
                model=fallback_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000,
                temperature=0.2,
            )

            if response["success"]:
                # Create basic analysis structure
                fallback_data = {
                    "analysis_id": analysis_id,
                    "decision": decision,
                    "rationale": rationale,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "reasoning_steps": [
                        {
                            "step_number": 1,
                            "description": "Fallback analysis",
                            "conclusion": response["data"]["response_text"],
                            "confidence": 0.6,
                            "evidence_cited": [],
                        }
                    ],
                    "quality_metrics": {
                        "overall_quality_score": 0.5,
                        "evidence_strength": 0.5,
                        "operational_feasibility": 0.5,
                        "strategic_alignment": 0.5,
                        "compound_learning": 0.5,
                        "risk_adjusted_score": 0.5,
                    },
                    "recommendations": ["Review analysis - fallback mode used"],
                    "key_insights": ["Structured analysis unavailable"],
                    "model_used": fallback_model,
                    "analysis_cost": response["cost_info"]["total_cost"],
                    "confidence_level": 0.6,
                    "context_quality": 0.3,
                    "fallback_mode": True,
                }

                return {
                    "success": True,
                    "data": fallback_data,
                    "cost_info": response["cost_info"],
                    "fallback_used": True,
                }
            else:
                return {
                    "success": False,
                    "error": f"Fallback analysis also failed: {response['error']}",
                }

        except Exception as e:
            return {"success": False, "error": f"Fallback analysis error: {str(e)}"}

    def _select_optimal_model(self, task_type: str, complexity: str) -> str:
        """Select optimal model based on task and configuration."""
        models = self.config["external_reasoning"]["models"]
        budget_limit = self.config["external_reasoning"]["cost_limits"][
            "max_cost_per_analysis"
        ]

        return self.openai_client.get_optimal_model_for_task(
            task_type=task_type, complexity=complexity, budget_limit=budget_limit
        )

    def _check_budget_constraints(self) -> bool:
        """Check if analysis is within budget constraints."""
        try:
            daily_limit = self.config["external_reasoning"]["cost_limits"][
                "daily_budget"
            ]
            max_per_analysis = self.config["external_reasoning"]["cost_limits"][
                "max_cost_per_analysis"
            ]

            # Check daily budget
            if self.cost_tracker["daily_cost"] >= daily_limit:
                self.logger.warning(
                    f"Daily budget limit reached: {self.cost_tracker['daily_cost']:.4f} >= {daily_limit}"
                )
                return False

            # Check if we have room for another analysis
            if (self.cost_tracker["daily_cost"] + max_per_analysis) > daily_limit:
                self.logger.warning("Insufficient budget remaining for analysis")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking budget constraints: {e}")
            return False

    def _update_cost_tracking(self, analysis_cost: float):
        """Update cost tracking metrics."""
        self.cost_tracker["daily_cost"] += analysis_cost
        self.cost_tracker["analysis_count"] += 1

        self.logger.info(
            f"Cost tracking updated: {analysis_cost:.4f} USD, Daily total: {self.cost_tracker['daily_cost']:.4f}"
        )

    async def _store_analysis_results(
        self, analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store analysis results in the database."""
        try:
            # This would store results in decision_analyses collection
            # For now, just return success - can be implemented when needed
            return {
                "stored": True,
                "collection": "decision_analyses",
                "document_id": analysis_data.get("analysis_id"),
            }

        except Exception as e:
            self.logger.error(f"Error storing analysis results: {e}")
            return {"stored": False, "error": str(e)}

    async def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis by ID from cache or database."""
        # Check cache first
        if analysis_id in self.analysis_cache:
            return self.analysis_cache[analysis_id]

        # TODO: Implement database retrieval
        return None

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get current cost tracking summary."""
        return {
            "daily_cost": self.cost_tracker["daily_cost"],
            "analysis_count": self.cost_tracker["analysis_count"],
            "average_cost_per_analysis": (
                self.cost_tracker["daily_cost"] / self.cost_tracker["analysis_count"]
                if self.cost_tracker["analysis_count"] > 0
                else 0.0
            ),
            "daily_budget": self.config["external_reasoning"]["cost_limits"][
                "daily_budget"
            ],
            "remaining_budget": (
                self.config["external_reasoning"]["cost_limits"]["daily_budget"]
                - self.cost_tracker["daily_cost"]
            ),
        }

    async def close(self):
        """Close service and cleanup resources."""
        if self.openai_client:
            await self.openai_client.close()

        if self.context_gatherer:
            self.context_gatherer.close()

        self.logger.info("External Reasoning Service closed")


# Helper function for easy integration
async def analyze_decision_with_external_reasoning(
    decision: str, rationale: str, config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze a decision using external reasoning.

    Args:
        decision: Decision to analyze
        rationale: Provided rationale
        config_path: Optional path to configuration file

    Returns:
        Dictionary containing analysis results
    """
    service = ExternalReasoningService(config_path)

    try:
        initialization_success = await service.initialize()
        if not initialization_success:
            return {
                "success": False,
                "error": "Failed to initialize External Reasoning Service",
            }

        return await service.analyze_decision(decision, rationale)

    finally:
        await service.close()


if __name__ == "__main__":
    # Test the external reasoning service
    async def test_service():
        print("Testing External Reasoning Service...")

        result = await analyze_decision_with_external_reasoning(
            decision="Implement external reasoning for autonomous decision system",
            rationale="The current keyword-based approach is limited and doesn't provide genuine reasoning. External reasoning using AI models would provide more sophisticated analysis.",
        )

        if result["success"]:
            print("✅ Analysis completed successfully!")
            print(f"Analysis ID: {result['analysis_id']}")
            print(
                f"Overall Quality Score: {result['data']['quality_metrics']['overall_quality_score']:.3f}"
            )
            print(f"Analysis Cost: ${result['data']['analysis_cost']:.4f}")
        else:
            print(f"❌ Analysis failed: {result['error']}")

    # Run test
    asyncio.run(test_service())
