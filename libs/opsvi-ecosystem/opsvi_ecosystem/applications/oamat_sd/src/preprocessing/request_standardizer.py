"""
Request Standardizer - Intelligent Preprocessing Agent

This module takes raw user input and converts it into a standardized format
that the O3 master agent can reliably consume for optimal workflow generation.

Uses GPT-4.1-mini with structured outputs to intelligently analyze and fill
in missing details with reasonable assumptions.
"""

import json
from datetime import datetime
from typing import Any

from src.applications.oamat_sd.src.reasoning.structured_output_enforcer import (
    StructuredOutputEnforcer,
)
from src.applications.oamat_sd.src.reasoning.subdivision_analyzer import (
    SubdivisionAnalyzer,
)
from src.applications.oamat_sd.src.sd_logging import LoggerFactory
from src.applications.oamat_sd.src.sd_logging.log_config import default_config

from .schemas import (
    PreprocessingResult,
    RequestType,
    StandardizedRequest,
)


class RequestStandardizer:
    """
    Intelligent preprocessing agent that standardizes user requests.

    Analyzes raw user input and fills in a comprehensive StandardizedRequest
    schema with intelligent assumptions where information is missing.
    """

    def __init__(self, logger_factory: LoggerFactory = None):
        """Initialize the Request Standardizer with Subdivision Analysis"""
        self.logger_factory = logger_factory or LoggerFactory(default_config)
        self.logger = self.logger_factory.get_debug_logger()

        # Initialize structured output enforcer for reliable schema filling
        self.structured_enforcer = StructuredOutputEnforcer()

        # Initialize subdivision analyzer for O3-powered complexity analysis
        self.subdivision_analyzer = SubdivisionAnalyzer(logger_factory)

        # Model configuration - use GPT-4.1-mini for execution tasks
        self.model_config = {
            "model_name": "gpt-4.1-mini",
            "temperature": 0.2,  # Lower temperature for consistent analysis
            "max_tokens": 4000,
        }

        self.logger.info("✅ Request Standardizer initialized with subdivision analysis")

    async def standardize_request(
        self, raw_request: str, debug: bool = False
    ) -> PreprocessingResult:
        """
        Convert raw user request into standardized format.

        Args:
            raw_request: The original user input
            debug: Enable debug logging

        Returns:
            PreprocessingResult with standardized request or error information
        """
        start_time = datetime.now()

        try:
            if debug:
                self.logger.info(f"🔄 Preprocessing request: {raw_request[:100]}...")

            # Create comprehensive analysis prompt
            analysis_prompt = self._create_standardization_prompt(raw_request)

            if debug:
                self.logger.info("🧠 Analyzing request with GPT-4.1-mini...")

            # Use structured output enforcement to ensure valid schema
            standardization_result = (
                await self.structured_enforcer.enforce_request_standardization(
                    prompt=analysis_prompt,
                    model_config=self.model_config,
                    context={
                        "original_request": raw_request,
                        "timestamp": datetime.now().isoformat(),
                        "debug": debug,
                    },
                )
            )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            if debug:
                self.logger.info(
                    f"✅ Request standardization complete in {processing_time:.0f}ms"
                )

            # Handle different response structures
            if standardization_result.get("success"):
                # Extract the actual result from the structured response
                if "result" in standardization_result:
                    actual_result = standardization_result["result"]
                else:
                    actual_result = standardization_result

                # Create StandardizedRequest from the actual result
                standardized_request = StandardizedRequest(**actual_result)

                if debug:
                    self.logger.info(
                        f"🏷️  Classified as: {standardized_request.classification.request_type}"
                    )
                    self.logger.info(
                        f"🔧 Complexity: {standardized_request.classification.complexity_level}"
                    )

                # Enhanced preprocessing: Add subdivision analysis
                if debug:
                    self.logger.info(
                        "🧠 O3 SUBDIVISION ANALYSIS: Starting complexity analysis for subdivision..."
                    )

                try:
                    # Analyze subdivision requirements using O3 reasoning
                    subdivision_metadata = await self.subdivision_analyzer.analyze_subdivision_requirements(
                        standardized_request, debug=debug
                    )

                    # Analyze domain specializations
                    domain_specializations = (
                        await self.subdivision_analyzer.analyze_domain_specializations(
                            standardized_request, debug=debug
                        )
                    )

                    # Update the standardized request with subdivision analysis
                    standardized_request.subdivision_metadata = subdivision_metadata
                    standardized_request.domain_specializations = domain_specializations

                    if debug:
                        self.logger.info(
                            "✅ Subdivision analysis integrated into preprocessing"
                        )
                        if subdivision_metadata.requires_subdivision:
                            self.logger.info(
                                f"🔄 SUBDIVISION RECOMMENDED: {subdivision_metadata.subdivision_reasoning[:100]}..."
                            )
                        else:
                            self.logger.info(
                                "📝 LINEAR WORKFLOW RECOMMENDED: No subdivision needed"
                            )

                except Exception as e:
                    self.logger.warning(
                        f"⚠️  Subdivision analysis failed, continuing without: {e}"
                    )
                    # Continue with basic standardized request if subdivision analysis fails

                return PreprocessingResult(
                    success=True,
                    standardized_request=standardized_request,
                    processing_time_ms=processing_time,
                    model_used=self.model_config["model_name"],
                )
            else:
                # Handle failure case
                error_message = standardization_result.get("error", "Unknown error")
                self.logger.error(f"❌ Standardization failed: {error_message}")
                return PreprocessingResult(
                    success=False,
                    error_message=error_message,
                    processing_time_ms=processing_time,
                    model_used=self.model_config["model_name"],
                )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            self.logger.error(f"❌ Request standardization failed: {e}")

            return PreprocessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time,
                model_used=self.model_config["model_name"],
            )

    def _create_standardization_prompt(self, raw_request: str) -> str:
        """Create the comprehensive analysis prompt for request standardization"""

        # Provide examples of different request types to guide analysis
        request_type_examples = {
            "application_development": [
                "Create a web application",
                "Build a mobile app",
                "Develop a desktop application",
            ],
            "web_service": [
                "Create a REST API",
                "Build a microservice",
                "Develop a web service",
            ],
            "script_automation": [
                "Create a script to automate",
                "Build a tool that processes",
                "Automate the process of",
            ],
            "data_analysis": [
                "Analyze this dataset",
                "Create a data visualization",
                "Process and analyze data",
            ],
        }

        complexity_indicators = {
            "simple": [
                "single file",
                "basic",
                "simple",
                "quick",
                "straightforward",
                "hello world",
                "example",
                "demo",
            ],
            "moderate": [
                "multiple files",
                "with database",
                "authentication",
                "API integration",
                "user interface",
                "configuration",
                "testing",
            ],
            "complex": [
                "microservices",
                "distributed system",
                "architecture",
                "scalable",
                "enterprise",
                "production-ready",
                "full-featured",
            ],
        }

        prompt = f"""You are an intelligent request analysis agent. Your task is to analyze a raw user request and convert it into a comprehensive, standardized format that provides complete context for downstream processing.

## YOUR MISSION
Transform the user's request into a detailed StandardizedRequest that fills in ALL possible information, making intelligent assumptions where details are missing.

## ANALYSIS FRAMEWORK

### REQUEST CLASSIFICATION
Analyze the request type based on these patterns:
{json.dumps(request_type_examples, indent=2)}

### COMPLEXITY ASSESSMENT
Determine complexity based on these indicators:
{json.dumps(complexity_indicators, indent=2)}

### INTELLIGENT GAP FILLING
For any missing information, make reasonable assumptions based on:
- Request type and context
- Industry best practices
- Common technical patterns
- Typical user needs

## RAW USER REQUEST TO ANALYZE:
"{raw_request}"

## STANDARDIZATION REQUIREMENTS

**CRITICAL**: You MUST fill out the complete StandardizedRequest schema. For every field:
1. **Extract explicit information** from the user request
2. **Infer implicit requirements** based on context
3. **Make intelligent assumptions** for missing details
4. **Provide confidence scores** for your analysis

### CONFIDENCE SCORING GUIDELINES:
- **1.0**: Explicitly stated in request
- **0.8**: Clearly implied by context
- **0.6**: Reasonable assumption based on request type
- **0.4**: Best guess with limited information
- **0.2**: Uncertain assumption

### SPECIFIC REQUIREMENTS:

**Classification**: Determine the primary request type, complexity level, domain category, platform target, quality level, and estimated effort.

**Technical Specification**: Identify or assume programming languages, frameworks, platforms, databases, external services, and any constraints.

**Functional Requirements**: Break down the request into specific, testable functional requirements with acceptance criteria.

**Deliverables**: Specify what files, documentation, and artifacts should be created.

**Context**: Note any environmental constraints, user preferences, or integration requirements.

**Success Criteria**: Define what constitutes successful completion of this request.

## OUTPUT REQUIREMENTS
Return a complete JSON object that matches the StandardizedRequest schema exactly. Every field should be thoughtfully filled with either extracted information, intelligent inferences, or reasonable assumptions.

**REMEMBER**: The goal is to provide the downstream O3 master agent with rich, complete context so it can generate optimal workflows without having to guess at requirements.

Generate the complete standardized request JSON:"""

        return prompt

    def validate_standardized_request(
        self, standardized_request: StandardizedRequest
    ) -> dict[str, Any]:
        """
        Validate the quality and completeness of a standardized request.

        Returns:
            Validation report with recommendations
        """
        validation_report = {
            "is_valid": True,
            "completeness_score": 0.0,
            "quality_issues": [],
            "recommendations": [],
            "confidence_analysis": {},
        }

        try:
            # Check completeness
            completeness_factors = []

            # Classification completeness
            if standardized_request.classification.request_type != RequestType.OTHER:
                completeness_factors.append(1.0)
            else:
                completeness_factors.append(0.5)
                validation_report["quality_issues"].append(
                    "Request type classified as 'other' - may need more specific classification"
                )

            # Technical specification completeness
            tech_spec = standardized_request.technical_specification
            if (
                tech_spec.programming_languages
                or tech_spec.frameworks
                or tech_spec.platforms
            ):
                completeness_factors.append(1.0)
            else:
                completeness_factors.append(0.3)
                validation_report["quality_issues"].append(
                    "No technical specifications identified - may need more technical details"
                )

            # Requirements completeness
            if standardized_request.functional_requirements:
                completeness_factors.append(1.0)
            else:
                completeness_factors.append(0.5)
                validation_report["recommendations"].append(
                    "Consider adding more specific functional requirements"
                )

            # Deliverables completeness
            deliverables = standardized_request.deliverables
            if deliverables.file_types or deliverables.documentation_requirements:
                completeness_factors.append(1.0)
            else:
                completeness_factors.append(0.4)
                validation_report["recommendations"].append(
                    "Specify expected deliverables and file types"
                )

            # Calculate overall completeness
            validation_report["completeness_score"] = sum(completeness_factors) / len(
                completeness_factors
            )

            # Confidence analysis
            conf = standardized_request.confidence_scores
            validation_report["confidence_analysis"] = {
                "overall_confidence": conf.overall_confidence,
                "high_confidence_areas": [],
                "low_confidence_areas": [],
            }

            if conf.classification_confidence >= 0.8:
                validation_report["confidence_analysis"][
                    "high_confidence_areas"
                ].append("classification")
            elif conf.classification_confidence < 0.6:
                validation_report["confidence_analysis"]["low_confidence_areas"].append(
                    "classification"
                )

            if conf.technical_confidence >= 0.8:
                validation_report["confidence_analysis"][
                    "high_confidence_areas"
                ].append("technical_specification")
            elif conf.technical_confidence < 0.6:
                validation_report["confidence_analysis"]["low_confidence_areas"].append(
                    "technical_specification"
                )

            if conf.requirements_confidence >= 0.8:
                validation_report["confidence_analysis"][
                    "high_confidence_areas"
                ].append("requirements")
            elif conf.requirements_confidence < 0.6:
                validation_report["confidence_analysis"]["low_confidence_areas"].append(
                    "requirements"
                )

            # Overall quality assessment
            if (
                validation_report["completeness_score"] < 0.6
                or conf.overall_confidence < 0.6
            ):
                validation_report["is_valid"] = False
                validation_report["recommendations"].append(
                    "Consider requesting user clarification for low-confidence areas"
                )

        except Exception as e:
            validation_report["is_valid"] = False
            validation_report["quality_issues"].append(f"Validation error: {e}")

        return validation_report
