#!/usr/bin/env python3
"""
Subdivision Analyzer - O3-Powered Complexity Analysis

Analyzes standardized requests to determine if subdivision is beneficial
and generates dynamic subdivision metadata using O3-mini reasoning model.

Follows the same pattern as dynamic_config_generator.py with:
- O3-mini for complex analysis
- Structured output enforcement
- Dynamic generation (no hardcoded values)
- Integration with centralized configuration
"""

from pathlib import Path

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.preprocessing.schemas import (
    DomainSpecialization,
    StandardizedRequest,
    SubdivisionMetadata,
)
from src.applications.oamat_sd.src.reasoning.structured_output_enforcer import (
    StructuredOutputEnforcer,
)
from src.applications.oamat_sd.src.sd_logging import LoggerFactory
from src.applications.oamat_sd.src.sd_logging.log_config import default_config


class SubdivisionAnalyzer:
    """
    O3-Powered Subdivision Analysis Agent

    Uses O3-mini reasoning model to analyze request complexity and determine
    optimal subdivision strategies with dynamic metadata generation.
    """

    def __init__(self, logger_factory: LoggerFactory = None):
        """Initialize the Subdivision Analyzer"""
        self.logger_factory = logger_factory or LoggerFactory(default_config)
        self.logger = self.logger_factory.get_debug_logger()

        # Initialize structured output enforcer for O3 reasoning
        self.structured_enforcer = StructuredOutputEnforcer()

        # Configuration from centralized config manager (no hardcoded values)
        self.config_manager = ConfigManager()

        # O3-mini configuration for reasoning tasks
        self.model_config = {
            "model_name": self.config_manager.models["reasoning"].model_name,  # o3-mini
            "reasoning_effort": self.config_manager.models[
                "reasoning"
            ].reasoning_effort,  # medium
            "max_tokens": self.config_manager.models["reasoning"].max_tokens,  # 16000
        }

        self.logger.info("✅ Subdivision Analyzer initialized with O3-mini reasoning")

    async def analyze_subdivision_requirements(
        self, standardized_request: StandardizedRequest, debug: bool = False
    ) -> SubdivisionMetadata:
        """
        Analyze if subdivision would benefit this request using O3 reasoning

        Args:
            standardized_request: Preprocessed and standardized user request
            debug: Enable detailed logging

        Returns:
            SubdivisionMetadata with O3-generated analysis
        """
        if debug:
            self.logger.info(
                "🧠 O3 ANALYSIS: Starting subdivision requirement analysis..."
            )

        # Load subdivision analysis prompt
        config_dir = Path(__file__).parent.parent.parent / "config"

        # Load O3 subdivision analysis prompt
        prompt_path = config_dir / "subdivision_analysis_prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Subdivision analysis prompt not found: {prompt_path}"
            )

        with open(prompt_path) as f:
            analysis_prompt = f.read()

        # Prepare comprehensive context for O3 analysis
        request_context = self._build_analysis_context(standardized_request)

        # Enhanced O3 analysis prompt with request context
        o3_analysis_prompt = f"""
{analysis_prompt}

## REQUEST ANALYSIS CONTEXT:
{request_context}

## YOUR ANALYSIS TASK:
Analyze this standardized request for subdivision opportunities and generate complete subdivision metadata.

Focus your O3 reasoning on:
1. **Complexity Assessment**: Multi-factor complexity analysis (cognitive, technical, integration, domain, resource, timeline)
2. **Subdivision Benefits**: Identify specific benefits from task decomposition
3. **Coordination Analysis**: Estimate coordination overhead vs. parallelization gains
4. **Role Specialization**: Suggest specialized agent roles for subdivided components
5. **Integration Requirements**: Determine how subdivided components should integrate

**CRITICAL**: Your generated JSON must match the subdivision_metadata schema exactly.
Generate ALL fields dynamically - no assumptions about default values.

Return ONLY the subdivision metadata JSON - no other text.
"""

        try:
            if debug:
                self.logger.info(
                    "🔒 O3 REASONING: Calling subdivision analysis with structured enforcement..."
                )

            # O3 subdivision analysis with structured output enforcement
            subdivision_result = (
                await self.structured_enforcer.enforce_subdivision_metadata(
                    prompt=o3_analysis_prompt,
                    model_config=self.model_config,
                    context={
                        "standardized_request": standardized_request.model_dump(),
                        "debug": debug,
                    },
                )
            )

            if debug:
                self.logger.info(
                    "📊 O3 ANALYSIS: Subdivision metadata generation complete!"
                )
                self.logger.info(
                    f"🔍 Analysis result keys: {list(subdivision_result.keys())}"
                )

            # Convert to SubdivisionMetadata object
            subdivision_metadata = SubdivisionMetadata(**subdivision_result)

            if debug:
                self._display_subdivision_analysis(
                    subdivision_metadata, standardized_request
                )

            return subdivision_metadata

        except Exception as e:
            self.logger.error(f"❌ Subdivision analysis failed: {e}")
            if debug:
                self.logger.error(f"🔄 O3 reasoning error: {e}")

            # NO HARDCODED FALLBACKS - Fail fast as designed
            raise RuntimeError(
                f"Subdivision analysis failed: {e}. System cannot proceed without valid O3-generated analysis."
            )

    def _build_analysis_context(self, request: StandardizedRequest) -> str:
        """Build comprehensive context for O3 subdivision analysis"""

        # Extract key request characteristics
        complexity_level = request.classification.complexity_level.value
        request_type = request.classification.request_type.value
        domain_category = request.classification.domain_category
        estimated_effort = request.classification.estimated_effort

        # Build context sections
        context_sections = [
            f"**REQUEST TYPE**: {request_type}",
            f"**COMPLEXITY LEVEL**: {complexity_level}",
            f"**DOMAIN CATEGORY**: {domain_category}",
            f"**ESTIMATED EFFORT**: {estimated_effort} hours",
            f"**CONFIDENCE SCORE**: {request.confidence_scores.overall_confidence:.2f}/1.0",
        ]

        # Add technical requirements if available
        if request.technical_specification:
            tech_reqs = request.technical_specification
            if tech_reqs.programming_languages:
                context_sections.append(
                    f"**LANGUAGES**: {', '.join(tech_reqs.programming_languages)}"
                )
            if tech_reqs.frameworks:
                context_sections.append(
                    f"**FRAMEWORKS**: {', '.join(tech_reqs.frameworks)}"
                )

        # Add functional requirements complexity
        if request.functional_requirements:
            req_count = len(request.functional_requirements)
            context_sections.append(
                f"**FUNCTIONAL REQUIREMENTS**: {req_count} requirements identified"
            )

        # Add deliverables complexity
        if request.deliverables:
            deliverables = request.deliverables
            file_types = len(deliverables.file_types) if deliverables.file_types else 0
            docs_needed = (
                len(deliverables.documentation_requirements)
                if deliverables.documentation_requirements
                else 0
            )
            context_sections.append(
                f"**DELIVERABLES**: {file_types} file types, {docs_needed} documentation items"
            )

        # Add parallel work opportunities context
        if (
            hasattr(request, "parallel_work_opportunities")
            and request.parallel_work_opportunities
        ):
            context_sections.append(
                f"**PARALLEL OPPORTUNITIES**: {len(request.parallel_work_opportunities)} identified"
            )

        return "\n".join(context_sections)

    def _display_subdivision_analysis(
        self, metadata: SubdivisionMetadata, request: StandardizedRequest
    ) -> None:
        """Display subdivision analysis results for debugging"""

        self.logger.info("🔍 SUBDIVISION ANALYSIS RESULTS:")
        self.logger.info(f"   📊 Complexity Score: {metadata.complexity_score}/10.0")
        self.logger.info(f"   🔄 Requires Subdivision: {metadata.requires_subdivision}")

        if metadata.subdivision_reasoning:
            self.logger.info(
                f"   💭 Reasoning: {metadata.subdivision_reasoning[:100]}..."
            )

        if metadata.suggested_sub_roles:
            self.logger.info(
                f"   👥 Suggested Roles: {', '.join(metadata.suggested_sub_roles)}"
            )

        if metadata.parallelization_potential:
            self.logger.info(
                f"   ⚡ Parallelization Potential: {metadata.parallelization_potential:.2f}"
            )

        if metadata.coordination_overhead:
            self.logger.info(
                f"   🔗 Coordination Overhead: {metadata.coordination_overhead:.2f}"
            )

        if metadata.max_subdivision_depth:
            self.logger.info(f"   📏 Max Depth: {metadata.max_subdivision_depth}")

    async def analyze_domain_specializations(
        self, standardized_request: StandardizedRequest, debug: bool = False
    ) -> list[DomainSpecialization]:
        """
        Analyze domain specialization requirements using O3 reasoning

        Args:
            standardized_request: Preprocessed request
            debug: Enable detailed logging

        Returns:
            List of domain specializations for subdivision
        """
        if debug:
            self.logger.info(
                "🧠 O3 ANALYSIS: Analyzing domain specialization requirements..."
            )

        # Use O3 to identify domain specializations needed for subdivision
        domain_analysis_prompt = f"""
You are an expert system architect analyzing domain specialization requirements.

TASK: Analyze this request to identify domain specializations that would benefit from dedicated agents in a subdivision approach.

REQUEST CONTEXT:
- Type: {standardized_request.classification.request_type.value}
- Complexity: {standardized_request.classification.complexity_level.value}
- Domain: {standardized_request.classification.domain_category}
- Technologies: {standardized_request.key_technologies}

Generate a JSON array of domain specializations, each with:
- domain_name: Specific domain name
- expertise_level: Required expertise (basic/intermediate/advanced/expert)
- key_technologies: Core technologies for this domain
- integration_points: How this domain integrates with others
- specialization_benefits: Why this domain benefits from specialization

Return ONLY the JSON array of domain specializations.
"""

        try:
            # Call O3 for domain specialization analysis
            specializations_result = await self.structured_enforcer.enforce_json_output(
                prompt=domain_analysis_prompt,
                model_config=self.model_config,
                context={"request": standardized_request.model_dump()},
            )

            # Convert to DomainSpecialization objects
            specializations = [
                DomainSpecialization(**spec) for spec in specializations_result
            ]

            if debug:
                self.logger.info(
                    f"🎯 Identified {len(specializations)} domain specializations"
                )
                for spec in specializations:
                    self.logger.info(
                        f"   🏷️  {spec.domain_name} ({spec.expertise_level})"
                    )

            return specializations

        except Exception as e:
            self.logger.error(f"❌ Domain specialization analysis failed: {e}")
            # Return empty list rather than failing (graceful degradation for this feature)
            return []
