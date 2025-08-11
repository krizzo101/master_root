"""
Solution Synthesis Module

Handles combining agent outputs into coherent final solutions.
Extracted from smart_decomposition_agent.py for better modularity.
"""

from datetime import datetime
from typing import Any, Dict

from langchain_openai import ChatOpenAI

from src.applications.oamat_sd.src.models.workflow_models import SmartDecompositionState
from src.applications.oamat_sd.src.sd_logging import LoggerFactory


class SolutionSynthesisEngine:
    """Handles synthesis of agent outputs into final solutions"""

    def __init__(self, logger_factory: LoggerFactory, openai_client):
        self.logger_factory = logger_factory
        self.logger = logger_factory.get_debug_logger()
        self.openai_client = openai_client

        # Initialize reasoning model for synthesis - NO HARDCODED VALUES
        from src.applications.oamat_sd.src.config.config_manager import ConfigManager

        reasoning_config = ConfigManager().get_model_config("reasoning")

        self.reasoning_model = ChatOpenAI(
            model=reasoning_config.model_name,
            max_tokens=reasoning_config.max_tokens,
            client=openai_client,
        )

    async def synthesize_final_solution(
        self, state: SmartDecompositionState
    ) -> SmartDecompositionState:
        """Synthesize final solution from all agent outputs using O3 reasoning"""
        agent_outputs = state.get("agent_outputs", {})
        if not agent_outputs:
            raise RuntimeError(
                "No agent outputs available for synthesis. Cannot proceed without agent results."
            )

        self.logger.info("Synthesizing final solution from agent outputs...")

        synthesis_start_time = datetime.now()

        try:
            # Enhanced logging: Log synthesis process start
            self.logger_factory.log_component_operation(
                component="synthesis_process",
                operation="synthesis_start",
                data={
                    "agent_outputs_count": len(agent_outputs),
                    "total_agents": len(agent_outputs),
                    "agent_outputs_size": sum(
                        len(str(output)) for output in agent_outputs.values()
                    ),
                    "synthesis_model": "o3-mini",
                    "execution_started": True,
                },
            )

            # Create synthesis prompt
            synthesis_prompt = self._create_synthesis_prompt(
                state.get("user_request", ""), agent_outputs
            )

            # Execute O3 reasoning for synthesis
            response = await self.reasoning_model.ainvoke(synthesis_prompt)

            # Calculate synthesis execution time
            synthesis_execution_time = (
                datetime.now() - synthesis_start_time
            ).total_seconds() * 1000

            # Create final solution structure
            final_solution = {
                "artifact_type": self._determine_artifact_type(
                    state.get("user_request", "")
                ),
                "content": response.content,
                "supporting_files": {},  # Would extract from agent outputs
                "validation_results": self._validate_solution(response.content),
                "success": True,
                "synthesis_reasoning": response.content,
                "agent_contributions": agent_outputs,
            }

            # Enhanced logging: Log synthesis completion with quality metrics
            self.logger_factory.log_component_operation(
                component="synthesis_process",
                operation="synthesis_complete",
                data={
                    "synthesis_successful": True,
                    "execution_time_ms": synthesis_execution_time,
                    "solution_length": len(response.content),
                    "artifact_type": final_solution["artifact_type"],
                    "validation_results": final_solution["validation_results"],
                    "agent_contributions_count": len(agent_outputs),
                    "solution_quality_score": self._calculate_synthesis_quality(
                        final_solution, agent_outputs
                    ),
                },
                execution_time_ms=synthesis_execution_time,
                success=True,
            )

            state["final_solution"] = final_solution
            self.logger.info("Solution synthesis complete")

        except Exception as e:
            # Calculate execution time for failed synthesis
            synthesis_execution_time = (
                datetime.now() - synthesis_start_time
            ).total_seconds() * 1000

            # Enhanced logging: Log synthesis failure with error details
            self.logger_factory.log_component_operation(
                component="synthesis_process",
                operation="synthesis_failed",
                data={
                    "failure_reason": "execution_error",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "execution_time_ms": synthesis_execution_time,
                    "agent_outputs_available": bool(state.get("agent_outputs", {})),
                    "total_agents": len(state.get("agent_outputs", {})),
                    "synthesis_started": True,
                },
                execution_time_ms=synthesis_execution_time,
                success=False,
            )

            self.logger.error(f"Solution synthesis failed: {e}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Synthesis error: {e}")

            # NO FALLBACKS RULE: System must fail completely
            raise RuntimeError(
                f"Solution synthesis failed: {e}. Cannot proceed without proper O3 synthesis."
            )

        return state

    def _create_synthesis_prompt(
        self, user_request: str, agent_outputs: Dict[str, Any]
    ) -> str:
        """Create a comprehensive synthesis prompt for O3 reasoning"""

        # Prepare agent outputs summary
        outputs_summary = []
        for agent_role, output in agent_outputs.items():
            # Output is the raw string content from the agent, not a dict
            if output and isinstance(output, str) and len(output.strip()) > 0:
                outputs_summary.append(
                    f"""
**{agent_role.upper()} AGENT OUTPUT:**
{output}
"""
                )
            else:
                outputs_summary.append(
                    f"""
**{agent_role.upper()} AGENT FAILED:**
                Error: No output generated or empty response
"""
                )

        synthesis_prompt = f"""You are O3, an advanced reasoning system tasked with synthesizing multiple agent outputs into a comprehensive, coherent final solution.

## ORIGINAL USER REQUEST
{user_request}

## AGENT OUTPUTS TO SYNTHESIZE
{chr(10).join(outputs_summary)}

## YOUR SYNTHESIS MISSION

### 1. COMPREHENSIVE ANALYSIS
- Analyze all agent outputs for quality, completeness, and coherence
- Identify complementary elements that work together
- Note any conflicts or gaps between outputs
- Assess overall coverage of the user request

### 2. INTELLIGENT INTEGRATION
- Combine the best elements from each agent output
- Resolve any conflicts through reasoning
- Fill gaps where agents missed requirements
- Create a unified, coherent solution

### 3. SOLUTION ENHANCEMENT
- Improve code quality and documentation
- Add missing implementation details
- Ensure best practices are followed
- Validate technical accuracy

### 4. FINAL DELIVERABLE STRUCTURE

Provide a complete solution that includes:

#### EXECUTIVE SUMMARY
Brief overview of what was accomplished and how it addresses the user request.

#### COMPLETE IMPLEMENTATION
- All code files with proper structure
- Configuration files
- Documentation
- Setup instructions

#### TECHNICAL DETAILS
- Architecture decisions and rationale
- Implementation approach
- Key features and functionality
- Quality assurance measures

#### VALIDATION RESULTS
- How the solution meets the original requirements
- Testing recommendations
- Deployment considerations

### 5. QUALITY STANDARDS
- All code must be production-ready
- Documentation must be comprehensive
- Solution must be complete and functional
- Best practices must be followed throughout

### 6. OUTPUT FORMAT
Structure your response as a complete, professional solution that could be delivered to a client. Include all necessary files, explanations, and implementation details.

## SYNTHESIS REQUIREMENTS
- Synthesize, don't just concatenate
- Apply critical reasoning to improve outputs
- Ensure completeness and quality
- Address the full scope of the user request

Now apply your advanced reasoning capabilities to create the perfect synthesized solution."""

        return synthesis_prompt

    def _determine_artifact_type(self, user_request: str) -> str:
        """Determine the type of artifact being created"""
        request_lower = user_request.lower()

        if any(
            word in request_lower for word in ["app", "application", "website", "web"]
        ):
            return "application"
        elif any(word in request_lower for word in ["api", "service", "backend"]):
            return "api_service"
        elif any(word in request_lower for word in ["script", "automation", "tool"]):
            return "script_tool"
        elif any(word in request_lower for word in ["analysis", "report", "study"]):
            return "analysis_report"
        elif any(word in request_lower for word in ["design", "architecture", "plan"]):
            return "design_document"
        else:
            return "general_solution"

    def _validate_solution(self, solution_content: str) -> Dict[str, Any]:
        """Validate the synthesized solution"""
        validation_results = {
            "completeness_score": 0.0,
            "quality_indicators": [],
            "potential_issues": [],
            "recommendations": [],
        }

        # Check for code blocks - NO HARDCODED VALUES
        from src.applications.oamat_sd.src.config.config_manager import ConfigManager

        config_manager = ConfigManager()

        if "```" in solution_content:
            validation_results["quality_indicators"].append(
                "Contains code implementations"
            )
            validation_results[
                "completeness_score"
            ] += config_manager.synthesis.completeness_scoring["code_blocks_bonus"]

        # Check for documentation
        if any(
            word in solution_content.lower()
            for word in ["documentation", "readme", "instructions"]
        ):
            validation_results["quality_indicators"].append("Includes documentation")
            validation_results[
                "completeness_score"
            ] += config_manager.synthesis.completeness_scoring["documentation_bonus"]

        # Check for structure
        if any(
            word in solution_content.lower()
            for word in ["architecture", "design", "structure"]
        ):
            validation_results["quality_indicators"].append(
                "Includes architectural considerations"
            )
            validation_results[
                "completeness_score"
            ] += config_manager.synthesis.completeness_scoring["architecture_bonus"]

        # Check for implementation details
        if any(
            word in solution_content.lower()
            for word in ["implementation", "setup", "installation"]
        ):
            validation_results["quality_indicators"].append(
                "Provides implementation guidance"
            )
            validation_results[
                "completeness_score"
            ] += config_manager.synthesis.completeness_scoring["implementation_bonus"]

        # Check length (indicator of thoroughness)
        if (
            len(solution_content)
            > config_manager.synthesis.completeness_scoring[
                "minimum_comprehensive_length"
            ]
        ):
            validation_results["quality_indicators"].append("Comprehensive response")
            validation_results[
                "completeness_score"
            ] += config_manager.synthesis.completeness_scoring["comprehensive_bonus"]

        # Potential issues
        if len(solution_content) < 500:
            validation_results["potential_issues"].append("Solution may be too brief")

        if "error" in solution_content.lower():
            validation_results["potential_issues"].append(
                "May contain error references"
            )

        # Recommendations
        if validation_results["completeness_score"] < 0.7:
            validation_results["recommendations"].append(
                "Consider adding more implementation details"
            )

        if not validation_results["quality_indicators"]:
            validation_results["recommendations"].append(
                "Ensure solution includes concrete deliverables"
            )

        return validation_results

    def _calculate_synthesis_quality(
        self, final_solution: Dict[str, Any], agent_outputs: Dict[str, Any]
    ) -> float:
        """Calculate the quality score of the synthesized solution"""
        from src.applications.oamat_sd.src.config.config_manager import ConfigManager

        config_manager = ConfigManager()

        quality_score = 0.0  # Initialize base quality score

        # Base score from validation - NO FALLBACKS
        if "validation_results" not in final_solution:
            raise RuntimeError(
                "validation_results missing from final_solution - NO FALLBACKS ALLOWED"
            )
        if "completeness_score" not in final_solution["validation_results"]:
            raise RuntimeError(
                "completeness_score missing from validation_results - NO FALLBACKS ALLOWED"
            )

        validation_score = final_solution["validation_results"]["completeness_score"]
        quality_score += (
            validation_score
            * config_manager.synthesis.quality_scoring_weights["content_completeness"]
        )

        # Agent contribution score - NO FALLBACKS
        # Since outputs are strings (not dicts), assume success if output exists and has content
        successful_agents = sum(
            1
            for output in agent_outputs.values()
            if output and isinstance(output, str) and len(output.strip()) > 0
        )
        total_agents = len(agent_outputs)
        if total_agents > 0:
            agent_success_ratio = successful_agents / total_agents
            quality_score += (
                agent_success_ratio
                * config_manager.synthesis.quality_scoring_weights["technical_accuracy"]
            )

        # Content length score (normalized) - NO HARDCODED VALUES, NO FALLBACKS
        if "content" not in final_solution:
            raise RuntimeError(
                "content missing from final_solution - NO FALLBACKS ALLOWED"
            )

        content_length = len(final_solution["content"])
        normalization_factor = config_manager.synthesis.completeness_scoring[
            "quality_length_normalization"
        ]
        length_score = min(content_length / normalization_factor, 1.0)
        quality_score += (
            length_score
            * config_manager.synthesis.quality_scoring_weights[
                "implementation_feasibility"
            ]
        )

        # Complexity score (more detailed solutions score higher)
        content = (
            final_solution.get("content") if "content" in final_solution else ""
        ).lower()
        complexity_indicators = [
            "implementation",
            "architecture",
            "design",
            "code",
            "configuration",
            "documentation",
            "testing",
            "deployment",
            "security",
            "performance",
        ]
        complexity_score = sum(
            1 for indicator in complexity_indicators if indicator in content
        )
        normalized_complexity = min(complexity_score / len(complexity_indicators), 1.0)
        quality_score += normalized_complexity * 0.1

        return round(min(quality_score, 1.0), 2)
