#!/usr/bin/env python3
"""
Subdivision Result Integrator - Intelligent Multi-Agent Output Synthesis

Integrates outputs from subdivision agents using O3 reasoning:
- Cross-domain result synthesis
- Conflict resolution between agents
- Quality assessment and validation
- Coherent final solution generation
- Performance optimization for subdivision workflows

Uses O3-mini for intelligent integration decisions and quality scoring.
"""

from datetime import datetime
from typing import Any

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.workflow_models import SmartDecompositionState
from src.applications.oamat_sd.src.reasoning.structured_output_enforcer import (
    StructuredOutputEnforcer,
)
from src.applications.oamat_sd.src.sd_logging import LoggerFactory
from src.applications.oamat_sd.src.sd_logging.log_config import default_config


class SubdivisionIntegrationResult:
    """Result of subdivision integration with quality metrics"""

    def __init__(
        self,
        integrated_solution: str,
        quality_score: float,
        integration_confidence: float,
        agent_contributions: dict[str, dict],
        conflicts_resolved: list[str],
        integration_reasoning: str,
        performance_metrics: dict[str, Any],
    ):
        self.integrated_solution = integrated_solution
        self.quality_score = quality_score
        self.integration_confidence = integration_confidence
        self.agent_contributions = agent_contributions
        self.conflicts_resolved = conflicts_resolved
        self.integration_reasoning = integration_reasoning
        self.performance_metrics = performance_metrics
        self.created_at = datetime.now()


class SubdivisionResultIntegrator:
    """
    Intelligent integration of subdivision agent outputs using O3 reasoning

    Capabilities:
    - Cross-domain result synthesis
    - Conflict detection and resolution
    - Quality assessment and scoring
    - Performance optimization
    - Coherent solution generation
    """

    def __init__(self, logger_factory: LoggerFactory = None):
        """Initialize the Subdivision Result Integrator"""
        self.logger_factory = logger_factory or LoggerFactory(default_config)
        self.logger = self.logger_factory.get_debug_logger()

        # Configuration from centralized config manager
        self.config_manager = ConfigManager()

        # O3 reasoning for integration analysis
        self.structured_enforcer = StructuredOutputEnforcer()

        # O3 reasoning configuration for integration
        self.reasoning_model_config = {
            "model_name": self.config_manager.models["reasoning"].model_name,  # o3-mini
            "reasoning_effort": self.config_manager.models[
                "reasoning"
            ].reasoning_effort,  # medium
            "max_tokens": self.config_manager.models["reasoning"].max_tokens,  # 16000
        }

        self.logger.info(
            "✅ Subdivision Result Integrator initialized with O3 reasoning"
        )

    async def integrate_subdivision_results(
        self, state: SmartDecompositionState, debug: bool = False
    ) -> SubdivisionIntegrationResult:
        """
        Integrate subdivision agent outputs into coherent final solution

        Args:
            state: Current execution state with subdivision outputs
            debug: Enable detailed logging

        Returns:
            SubdivisionIntegrationResult with integrated solution and metrics
        """
        if debug:
            self.logger.info(
                "🔄 SUBDIVISION INTEGRATOR: Starting intelligent result integration..."
            )

        integration_start_time = datetime.now()

        try:
            agent_outputs = state.get("agent_outputs", {})
            subdivision_metadata = state.get("context", {}).get(
                "subdivision_metadata", {}
            )

            if not agent_outputs:
                raise ValueError("No agent outputs to integrate")

            # Step 1: Analyze agent outputs for integration
            integration_analysis = await self._analyze_outputs_for_integration(
                agent_outputs, subdivision_metadata, debug
            )

            # Step 2: Detect and resolve conflicts
            conflict_resolution = await self._detect_and_resolve_conflicts(
                agent_outputs, integration_analysis, debug
            )

            # Step 3: Generate integrated solution using O3
            integrated_solution = await self._generate_integrated_solution(
                agent_outputs, integration_analysis, conflict_resolution, debug
            )

            # Step 4: Quality assessment and scoring
            quality_assessment = await self._assess_integration_quality(
                integrated_solution, agent_outputs, debug
            )

            # Calculate performance metrics
            integration_time = (
                datetime.now() - integration_start_time
            ).total_seconds() * 1000

            performance_metrics = {
                "integration_time_ms": integration_time,
                "agents_integrated": len(agent_outputs),
                "conflicts_detected": len(conflict_resolution.get("conflicts", [])),
                "resolution_strategies": conflict_resolution.get("strategies", []),
                "cross_domain_synthesis": integration_analysis.get(
                    "cross_domain_opportunities", 0
                ),
            }

            # Create integration result
            result = SubdivisionIntegrationResult(
                integrated_solution=integrated_solution["content"],
                quality_score=quality_assessment["quality_score"],
                integration_confidence=quality_assessment["confidence"],
                agent_contributions=integration_analysis["agent_contributions"],
                conflicts_resolved=conflict_resolution.get("resolved_conflicts", []),
                integration_reasoning=integrated_solution["reasoning"],
                performance_metrics=performance_metrics,
            )

            if debug:
                self.logger.info(f"✅ Integration complete in {integration_time:.0f}ms")
                self.logger.info(f"📊 Quality Score: {result.quality_score:.2f}/10.0")
                self.logger.info(f"🎯 Confidence: {result.integration_confidence:.2f}")

            return result

        except Exception as e:
            integration_time = (
                datetime.now() - integration_start_time
            ).total_seconds() * 1000
            self.logger.error(
                f"❌ Subdivision integration failed after {integration_time:.0f}ms: {e}"
            )
            raise RuntimeError(f"Integration failed: {e}")

    async def _analyze_outputs_for_integration(
        self,
        agent_outputs: dict[str, dict],
        subdivision_metadata: dict,
        debug: bool = False,
    ) -> dict[str, Any]:
        """Analyze agent outputs to identify integration opportunities and challenges"""

        if debug:
            self.logger.info(
                "🔍 ANALYSIS: Analyzing agent outputs for integration patterns..."
            )

        # Create comprehensive analysis prompt for O3
        analysis_prompt = f"""
You are an expert system integration analyst evaluating outputs from specialized subdivision agents.

## SUBDIVISION CONTEXT:
{subdivision_metadata}

## AGENT OUTPUTS TO INTEGRATE:
{self._format_agent_outputs_for_analysis(agent_outputs)}

## ANALYSIS TASK:

Analyze these subdivision agent outputs and provide:

1. **Agent Contribution Analysis**:
   - For each agent: domain, key contributions, quality indicators
   - Overlap detection between agent outputs
   - Unique value each agent provides

2. **Integration Opportunities**:
   - Cross-domain synthesis possibilities
   - Complementary outputs that can be combined
   - Areas where agent outputs enhance each other

3. **Integration Challenges**:
   - Conflicting approaches or recommendations
   - Inconsistent assumptions or requirements
   - Technical incompatibilities to resolve

4. **Quality Assessment**:
   - Individual agent output quality (1-10 scale)
   - Completeness of each contribution
   - Alignment with original subdivision goals

5. **Integration Strategy**:
   - Recommended approach for combining outputs
   - Priority order for integration
   - Risk factors to consider

Return a JSON object with this analysis structure.
"""

        try:
            analysis_result = await self.structured_enforcer.enforce_json_output(
                prompt=analysis_prompt,
                model_config=self.reasoning_model_config,
                context={
                    "agent_outputs": agent_outputs,
                    "subdivision_metadata": subdivision_metadata,
                    "debug": debug,
                },
            )

            if debug:
                self.logger.info(
                    f"🔍 Analysis complete: {len(analysis_result.get('agent_contributions', {}))} agents analyzed"
                )

            return analysis_result

        except Exception as e:
            self.logger.error(f"❌ Output analysis failed: {e}")
            raise RuntimeError(f"Failed to analyze outputs for integration: {e}")

    async def _detect_and_resolve_conflicts(
        self,
        agent_outputs: dict[str, dict],
        integration_analysis: dict[str, Any],
        debug: bool = False,
    ) -> dict[str, Any]:
        """Detect conflicts between agent outputs and generate resolution strategies"""

        if debug:
            self.logger.info(
                "⚖️ CONFLICT RESOLUTION: Detecting and resolving output conflicts..."
            )

        # Create conflict resolution prompt for O3
        conflict_prompt = f"""
You are an expert conflict resolution specialist for multi-agent system integration.

## INTEGRATION ANALYSIS:
{integration_analysis}

## CONFLICT DETECTION TASK:

Based on the integration analysis, identify and resolve conflicts:

1. **Conflict Identification**:
   - Technical approach conflicts
   - Requirement interpretation differences
   - Implementation strategy disagreements
   - Resource allocation conflicts

2. **Conflict Severity Assessment**:
   - Rate each conflict (low/medium/high/critical)
   - Impact on final solution quality
   - Difficulty of resolution

3. **Resolution Strategies**:
   - For each conflict, provide resolution approach
   - Preference for agent outputs (with reasoning)
   - Synthesis opportunities to resolve conflicts
   - Fallback strategies if resolution fails

4. **Integration Priority**:
   - Order for resolving conflicts
   - Dependencies between conflict resolutions
   - Risk mitigation strategies

Return a JSON object with conflict analysis and resolution plan.
"""

        try:
            conflict_result = await self.structured_enforcer.enforce_json_output(
                prompt=conflict_prompt,
                model_config=self.reasoning_model_config,
                context={
                    "agent_outputs": agent_outputs,
                    "integration_analysis": integration_analysis,
                    "debug": debug,
                },
            )

            if debug:
                conflicts_found = len(conflict_result.get("conflicts", []))
                self.logger.info(
                    f"⚖️ Conflict analysis complete: {conflicts_found} conflicts identified"
                )

            return conflict_result

        except Exception as e:
            self.logger.error(f"❌ Conflict resolution failed: {e}")
            raise RuntimeError(f"Failed to resolve conflicts: {e}")

    async def _generate_integrated_solution(
        self,
        agent_outputs: dict[str, dict],
        integration_analysis: dict[str, Any],
        conflict_resolution: dict[str, Any],
        debug: bool = False,
    ) -> dict[str, Any]:
        """Generate the integrated final solution using O3 reasoning"""

        if debug:
            self.logger.info("🔄 SYNTHESIS: Generating integrated solution using O3...")

        # Create solution synthesis prompt for O3
        synthesis_prompt = f"""
You are an expert solution architect creating a coherent final solution from subdivision agent outputs.

## INTEGRATION CONTEXT:
- Integration Analysis: {integration_analysis}
- Conflict Resolution: {conflict_resolution}

## AGENT OUTPUTS:
{self._format_agent_outputs_for_synthesis(agent_outputs)}

## SYNTHESIS TASK:

Create a comprehensive, coherent final solution that:

1. **Integrates All Agent Contributions**:
   - Combine the best elements from each agent
   - Respect the conflict resolution decisions
   - Maintain each agent's specialized expertise

2. **Maintains Solution Coherence**:
   - Ensure technical consistency across domains
   - Align implementation approaches
   - Create logical flow between components

3. **Optimizes Quality**:
   - Leverage complementary strengths
   - Address identified gaps or weaknesses
   - Enhance overall solution value

4. **Provides Clear Structure**:
   - Organize content logically
   - Maintain traceability to agent contributions
   - Include implementation guidance

Return a JSON object with:
- "content": The integrated solution text
- "reasoning": Explanation of integration decisions
- "agent_attribution": How each agent contributed
- "quality_indicators": Metrics for solution assessment
"""

        try:
            synthesis_result = await self.structured_enforcer.enforce_json_output(
                prompt=synthesis_prompt,
                model_config=self.reasoning_model_config,
                context={
                    "agent_outputs": agent_outputs,
                    "integration_analysis": integration_analysis,
                    "conflict_resolution": conflict_resolution,
                    "debug": debug,
                },
            )

            if debug:
                solution_length = len(synthesis_result.get("content", ""))
                self.logger.info(
                    f"🔄 Solution synthesis complete: {solution_length} characters generated"
                )

            return synthesis_result

        except Exception as e:
            self.logger.error(f"❌ Solution synthesis failed: {e}")
            raise RuntimeError(f"Failed to generate integrated solution: {e}")

    async def _assess_integration_quality(
        self,
        integrated_solution: dict[str, Any],
        agent_outputs: dict[str, dict],
        debug: bool = False,
    ) -> dict[str, Any]:
        """Assess the quality of the integrated solution"""

        if debug:
            self.logger.info(
                "📊 QUALITY ASSESSMENT: Evaluating integrated solution quality..."
            )

        # Create quality assessment prompt for O3
        quality_prompt = f"""
You are an expert quality assessor evaluating an integrated solution from subdivision agents.

## INTEGRATED SOLUTION:
{integrated_solution}

## ORIGINAL AGENT OUTPUTS:
{len(agent_outputs)} specialized agents contributed

## QUALITY ASSESSMENT TASK:

Evaluate the integrated solution across multiple dimensions:

1. **Content Quality (1-10)**:
   - Completeness and comprehensiveness
   - Technical accuracy and feasibility
   - Clarity and understandability

2. **Integration Quality (1-10)**:
   - How well agent outputs were combined
   - Consistency across domains
   - Coherence of final solution

3. **Value Added (1-10)**:
   - Improvement over individual outputs
   - Synergy between agent contributions
   - Overall solution effectiveness

4. **Confidence Assessment (0.0-1.0)**:
   - Confidence in integration decisions
   - Reliability of solution quality
   - Robustness of approach

Return a JSON object with quality scores and detailed assessment.
"""

        try:
            quality_result = await self.structured_enforcer.enforce_json_output(
                prompt=quality_prompt,
                model_config=self.reasoning_model_config,
                context={
                    "integrated_solution": integrated_solution,
                    "agent_outputs": agent_outputs,
                    "debug": debug,
                },
            )

            if debug:
                quality_score = quality_result.get("quality_score", 0)
                self.logger.info(
                    f"📊 Quality assessment complete: {quality_score:.1f}/10.0"
                )

            return quality_result

        except Exception as e:
            self.logger.error(f"❌ Quality assessment failed: {e}")
            raise RuntimeError(f"Failed to assess integration quality: {e}")

    def _format_agent_outputs_for_analysis(self, agent_outputs: dict[str, dict]) -> str:
        """Format agent outputs for O3 analysis"""
        formatted = []

        for agent_id, output in agent_outputs.items():
            role = output.get("role", "Unknown")
            specialization = output.get("specialization", "Unknown")
            content = output.get("content", "")[:500]  # Truncate for analysis

            formatted.append(
                f"""
Agent: {agent_id}
Role: {role}
Specialization: {specialization}
Content Preview: {content}...
"""
            )

        return "\n".join(formatted)

    def _format_agent_outputs_for_synthesis(
        self, agent_outputs: dict[str, dict]
    ) -> str:
        """Format agent outputs for solution synthesis"""
        formatted = []

        for agent_id, output in agent_outputs.items():
            role = output.get("role", "Unknown")
            specialization = output.get("specialization", "Unknown")
            content = output.get("content", "")

            formatted.append(
                f"""
== {agent_id} ({role}) ==
Specialization: {specialization}
Output:
{content}

"""
            )

        return "\n".join(formatted)

    def get_integration_metrics(
        self, result: SubdivisionIntegrationResult
    ) -> dict[str, Any]:
        """Get comprehensive metrics about the integration process"""

        return {
            "integration_mode": "subdivision_workflow",
            "quality_score": result.quality_score,
            "integration_confidence": result.integration_confidence,
            "agents_integrated": len(result.agent_contributions),
            "conflicts_resolved": len(result.conflicts_resolved),
            "integration_time_ms": result.performance_metrics.get(
                "integration_time_ms", 0
            ),
            "cross_domain_synthesis": result.performance_metrics.get(
                "cross_domain_synthesis", 0
            ),
            "solution_length": len(result.integrated_solution),
            "created_timestamp": result.created_at.isoformat(),
        }
