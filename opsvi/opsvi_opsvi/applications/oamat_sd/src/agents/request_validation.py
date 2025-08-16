"""
Request Validation - Modular Implementation

A clean, modular orchestrator for request validation using AI reasoning.
Coordinates specialized modules for validation, gap analysis, completion, and clarification.
"""

import logging
from typing import Any, Dict, List, Optional

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.interfaces.agent_interfaces import (
    IRequestValidationAgent,
)
from src.applications.oamat_sd.src.models.data_models import RequestInput
from src.applications.oamat_sd.src.models.validation_models import (
    ClarificationQuestion,
    CompletionResult,
    GapAnalysisResult,
    ValidationResult,
)
from src.applications.oamat_sd.src.validation.clarification_interface import (
    ClarificationInterface,
)
from src.applications.oamat_sd.src.validation.completion_engine import CompletionEngine
from src.applications.oamat_sd.src.validation.gap_analyzer import GapAnalyzer
from src.applications.oamat_sd.src.validation.schema_registry import (
    RequestSchemaRegistry,
)
from src.applications.oamat_sd.src.validation.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class RequestValidationAgent(IRequestValidationAgent):
    """
    Modular Request Validation using AI Reasoning

    This agent orchestrates the complete request validation workflow:
    1. Validation Engine -> AI-powered request type detection and information extraction
    2. Gap Analyzer -> Identify and prioritize missing information
    3. Completion Engine -> Fill gaps through research and defaults
    4. Clarification Interface -> Generate user-friendly clarification questions
    """

    def __init__(
        self,
        schema_registry: Optional[RequestSchemaRegistry] = None,
        model_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the Request Validation Agent with all modular components"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize registry first
        self.schema_registry = schema_registry or RequestSchemaRegistry()

        # Initialize modular components
        self.validation_engine = ValidationEngine(self.schema_registry, model_config)
        self.gap_analyzer = GapAnalyzer(self.schema_registry)
        self.completion_engine = CompletionEngine(self.schema_registry)
        self.clarification_interface = ClarificationInterface(model_config)

        self.logger.info(
            "✅ Request Validation Agent initialized with modular architecture"
        )

    async def validate_request(self, request: RequestInput) -> ValidationResult:
        """
        Perform comprehensive request validation using modular components

        Main orchestration method - implements IRequestValidationAgent interface
        """
        self.logger.info("🎯 Starting comprehensive request validation")

        try:
            # Extract request content
            request_content = self._extract_request_content(request)

            # Step 1: Core Validation - AI-powered or pattern-based
            self.logger.info("🔍 Step 1: Core Validation")
            validation_result = await self.validation_engine.validate_request(
                request_content
            )

            self.logger.info(
                f"✅ Validation complete: {validation_result.request_type}, "
                f"valid: {validation_result.is_valid}, "
                f"confidence: {validation_result.confidence:.2f}"
            )

            return validation_result

        except Exception as e:
            self.logger.error(f"❌ Request validation failed: {e}")
            # Return error result rather than failing completely
            return ValidationResult(
                request_type="unknown",
                is_valid=False,
                missing_fields=["validation_failed"],
                extracted_info={},
                confidence=0.0,
                validation_errors=[str(e)],
            )

    async def extract_information_dynamically(
        self, request: RequestInput
    ) -> Dict[str, Any]:
        """
        Use AI to extract information from natural language

        Interface method for dynamic information extraction
        """
        self.logger.info("📊 Starting dynamic information extraction")

        try:
            request_content = self._extract_request_content(request)
            validation_result = await self.validation_engine.validate_request(
                request_content
            )

            self.logger.info(
                f"✅ Extracted {len(validation_result.extracted_info)} information fields"
            )
            return validation_result.extracted_info

        except Exception as e:
            self.logger.error(f"❌ Information extraction failed: {e}")
            return {}

    async def generate_validation_strategy(self, content: str) -> Dict[str, Any]:
        """
        Dynamically generate validation approach for this specific content

        Interface method for validation strategy generation
        """
        self.logger.info("🎯 Generating validation strategy")

        try:
            # Run initial validation to understand the request
            validation_result = await self.validation_engine.validate_request(content)

            # Analyze gaps to determine completion strategy
            gap_analysis = self.gap_analyzer.analyze_gaps(validation_result)

            # Determine completion approach
            completion_difficulty = self.gap_analyzer.estimate_completion_difficulty(
                gap_analysis
            )

            strategy = {
                "request_type": validation_result.request_type,
                "validation_confidence": validation_result.confidence,
                "gaps_count": len(gap_analysis.gaps),
                "critical_gaps": gap_analysis.critical_gaps_count,
                "completion_difficulty": completion_difficulty,
                "researchable_gaps": len(gap_analysis.researchable_gaps),
                "recommended_approach": self._determine_recommended_approach(
                    gap_analysis
                ),
                "ai_enabled": self.validation_engine.ai_enabled,
            }

            self.logger.info(
                f"✅ Validation strategy generated: {strategy['recommended_approach']}"
            )
            return strategy

        except Exception as e:
            self.logger.error(f"❌ Strategy generation failed: {e}")
            return {"error": str(e), "recommended_approach": "manual_review"}

    async def analyze_gaps(
        self, validation_result: ValidationResult
    ) -> GapAnalysisResult:
        """Analyze information gaps and prioritize them for completion"""
        self.logger.info("🔍 Analyzing information gaps")
        return self.gap_analyzer.analyze_gaps(validation_result)

    async def complete_information(
        self, gap_analysis: GapAnalysisResult, request_type: str = "default"
    ) -> CompletionResult:
        """Complete missing information through research and defaults"""
        self.logger.info("🔧 Completing missing information")
        return await self.completion_engine.complete_information(
            gap_analysis, request_type
        )

    async def generate_clarification_questions(
        self, gap_analysis: GapAnalysisResult, original_request: str = ""
    ) -> List[ClarificationQuestion]:
        """Generate user-friendly clarification questions"""
        self.logger.info("❓ Generating clarification questions")

        # Get gaps that need user input
        user_input_gaps = [
            gap
            for gap in gap_analysis.gaps
            if not gap.researchable or gap.priority.value == "critical"
        ]

        if not user_input_gaps:
            return []

        return await self.clarification_interface.generate_clarification_questions(
            user_input_gaps,
            gap_analysis.gaps[0].field_name if gap_analysis.gaps else "unknown",
            original_request,
        )

    async def process_user_responses(
        self, user_input: str, questions: List[ClarificationQuestion]
    ) -> Dict[str, Any]:
        """Process user responses to clarification questions"""
        self.logger.info("📝 Processing user responses")
        return await self.clarification_interface.parse_user_responses(
            user_input, questions
        )

    async def complete_validation_workflow(
        self, request: RequestInput
    ) -> Dict[str, Any]:
        """
        Complete end-to-end validation workflow with all steps

        This is the main method for full validation processing
        """
        self.logger.info("🚀 Starting complete validation workflow")

        try:
            request_content = self._extract_request_content(request)

            # Step 1: Initial Validation
            validation_result = await self.validate_request(request)

            # Step 2: Gap Analysis
            gap_analysis = await self.analyze_gaps(validation_result)

            # Step 3: Information Completion
            completion_result = await self.complete_information(
                gap_analysis, validation_result.request_type
            )

            # Step 4: Generate Clarification Questions (if needed)
            clarification_questions = []
            if completion_result.escalation_required:
                clarification_questions = await self.generate_clarification_questions(
                    gap_analysis, request_content
                )

            # Compile workflow result
            workflow_result = {
                "validation": {
                    "request_type": validation_result.request_type,
                    "is_valid": validation_result.is_valid,
                    "confidence": validation_result.confidence,
                    "extracted_info": validation_result.extracted_info,
                    "missing_fields": validation_result.missing_fields,
                },
                "gap_analysis": {
                    "total_gaps": len(gap_analysis.gaps),
                    "critical_gaps": gap_analysis.critical_gaps_count,
                    "completeness_score": gap_analysis.completeness_score,
                    "difficulty": self.gap_analyzer.estimate_completion_difficulty(
                        gap_analysis
                    ),
                },
                "completion": {
                    "filled_fields": completion_result.filled_fields,
                    "applied_defaults": completion_result.applied_defaults,
                    "assumptions": completion_result.assumptions,
                    "escalation_required": completion_result.escalation_required,
                    "critical_gaps_remaining": completion_result.critical_gaps_remaining,
                },
                "clarification": {
                    "questions_needed": len(clarification_questions),
                    "questions": [
                        {
                            "field": q.field_name,
                            "question": q.question,
                            "importance": q.importance_explanation,
                            "options": q.options,
                        }
                        for q in clarification_questions
                    ],
                },
                "workflow_status": (
                    "complete"
                    if not completion_result.escalation_required
                    else "needs_clarification"
                ),
                "ai_enabled": self.validation_engine.ai_enabled,
            }

            self.logger.info(
                f"✅ Complete validation workflow finished: {workflow_result['workflow_status']}"
            )
            return workflow_result

        except Exception as e:
            self.logger.error(f"❌ Complete validation workflow failed: {e}")
            return {
                "workflow_status": "failed",
                "error": str(e),
                "ai_enabled": getattr(self.validation_engine, "ai_enabled", False),
            }

    def _extract_request_content(self, request: RequestInput) -> str:
        """Extract string content from request input"""
        if hasattr(request, "content"):
            return str(request.content)
        elif hasattr(request, "description"):
            return str(request.description)
        elif hasattr(request, "get"):
            # NO FALLBACKS - explicit validation required
            if "content" in request:
                return str(request["content"])
            elif "description" in request:
                return str(request["description"])
            else:
                return ConfigManager().analysis.request_processing[
                    "default_empty_content"
                ]
        else:
            return str(request)

    def _determine_recommended_approach(self, gap_analysis: GapAnalysisResult) -> str:
        """Determine the recommended approach based on gap analysis"""
        if gap_analysis.critical_gaps_count == 0:
            return "auto_complete"
        elif (
            gap_analysis.critical_gaps_count <= 2
            and len(gap_analysis.researchable_gaps) > 0
        ):
            return "research_and_clarify"
        elif gap_analysis.critical_gaps_count > 3:
            return "user_interview"
        else:
            return "iterative_clarification"

    def get_capabilities(self) -> Dict[str, Any]:
        """Return the capabilities of this validation agent"""
        return {
            "agent_name": "Request Validation Agent",
            "version": "2.0.0-modular",
            "architecture": "modular",
            "components": {
                "validation_engine": "AI-powered or pattern-based request validation",
                "gap_analyzer": "Information gap analysis and prioritization",
                "completion_engine": "Intelligent information completion",
                "clarification_interface": "User-friendly clarification generation",
                "schema_registry": "Request type schema management",
            },
            "features": [
                "AI-enhanced request validation",
                "Dynamic information extraction",
                "Intelligent gap analysis",
                "Automated information completion",
                "Natural language clarification questions",
                "Complete validation workflows",
                "Schema-based validation",
                "Pattern-based fallback validation",
            ],
            "supported_request_types": [
                rt.value for rt in self.schema_registry.list_schemas()
            ],
            "ai_enabled": self.validation_engine.ai_enabled,
            "modular_architecture": True,
        }
