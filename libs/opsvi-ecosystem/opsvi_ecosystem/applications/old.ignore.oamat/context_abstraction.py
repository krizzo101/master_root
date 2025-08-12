"""
OAMAT Context Abstraction System
Prevents information overload by intelligently filtering and summarizing
child workflow results appropriate for each hierarchical level.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class AbstractionLevel(Enum):
    """Defines the appropriate abstraction level for different hierarchical positions"""

    EXECUTIVE = 1  # High-level strategic overview
    MANAGERIAL = 2  # Mid-level tactical summary
    OPERATIONAL = 3  # Detailed implementation specifics
    TECHNICAL = 4  # Full technical details


class InformationType(Enum):
    """Categories of information for selective filtering"""

    STRATEGIC_DECISIONS = "strategic"
    TECHNICAL_ARCHITECTURE = "technical"
    IMPLEMENTATION_DETAILS = "implementation"
    ERROR_REPORTS = "errors"
    STATUS_UPDATES = "status"
    RESOURCE_USAGE = "resources"
    DEPENDENCIES = "dependencies"
    RISKS_BLOCKERS = "risks"


@dataclass
class ContextFilter:
    """Defines what information should be passed up to specific abstraction levels"""

    abstraction_level: AbstractionLevel
    included_types: list[InformationType]
    max_detail_length: int
    summary_style: str


class ChildWorkflowResult(BaseModel):
    """Structured result from child workflow"""

    workflow_id: str
    agent_role: str
    task_description: str
    completion_status: str
    key_decisions: list[str] = Field(default_factory=list)
    technical_details: dict[str, Any] = Field(default_factory=dict)
    dependencies_created: list[str] = Field(default_factory=list)
    risks_identified: list[str] = Field(default_factory=list)
    resource_usage: dict[str, Any] = Field(default_factory=dict)
    deliverables: list[str] = Field(default_factory=list)
    raw_output: str = ""


class AbstractedSummary(BaseModel):
    """Filtered and summarized information appropriate for parent level"""

    source_workflows: list[str]
    executive_summary: str
    key_outcomes: list[str]
    critical_dependencies: list[str]
    escalated_risks: list[str]
    resource_impact: str
    next_actions_required: list[str]
    confidence_level: float


class ContextAbstractionEngine:
    """
    Core engine for filtering and abstracting child workflow results
    for appropriate consumption by parent workflows
    """

    def __init__(self, llm_model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.1)
        self.abstraction_filters = self._initialize_filters()

    def _initialize_filters(self) -> dict[AbstractionLevel, ContextFilter]:
        """Initialize abstraction filters for different hierarchical levels"""
        return {
            AbstractionLevel.EXECUTIVE: ContextFilter(
                abstraction_level=AbstractionLevel.EXECUTIVE,
                included_types=[
                    InformationType.STRATEGIC_DECISIONS,
                    InformationType.RISKS_BLOCKERS,
                    InformationType.RESOURCE_USAGE,
                    InformationType.DEPENDENCIES,
                ],
                max_detail_length=200,
                summary_style="strategic_overview",
            ),
            AbstractionLevel.MANAGERIAL: ContextFilter(
                abstraction_level=AbstractionLevel.MANAGERIAL,
                included_types=[
                    InformationType.STRATEGIC_DECISIONS,
                    InformationType.TECHNICAL_ARCHITECTURE,
                    InformationType.RISKS_BLOCKERS,
                    InformationType.STATUS_UPDATES,
                    InformationType.DEPENDENCIES,
                ],
                max_detail_length=500,
                summary_style="tactical_summary",
            ),
            AbstractionLevel.OPERATIONAL: ContextFilter(
                abstraction_level=AbstractionLevel.OPERATIONAL,
                included_types=[
                    InformationType.TECHNICAL_ARCHITECTURE,
                    InformationType.IMPLEMENTATION_DETAILS,
                    InformationType.ERROR_REPORTS,
                    InformationType.DEPENDENCIES,
                    InformationType.RISKS_BLOCKERS,
                ],
                max_detail_length=1000,
                summary_style="operational_details",
            ),
            AbstractionLevel.TECHNICAL: ContextFilter(
                abstraction_level=AbstractionLevel.TECHNICAL,
                included_types=list(InformationType),  # All types
                max_detail_length=2000,
                summary_style="technical_comprehensive",
            ),
        }

    async def abstract_child_results(
        self,
        child_results: list[ChildWorkflowResult],
        parent_abstraction_level: AbstractionLevel,
        parent_context: str,
    ) -> AbstractedSummary:
        """
        Main method to filter and abstract child workflow results
        for appropriate parent consumption
        """

        # 1. Apply information filtering based on abstraction level
        filtered_results = self._filter_by_abstraction_level(
            child_results, parent_abstraction_level
        )

        # 2. Identify critical information that must bubble up
        critical_info = self._extract_critical_information(filtered_results)

        # 3. Generate abstracted summary using LLM
        abstracted_summary = await self._generate_intelligent_summary(
            filtered_results, critical_info, parent_abstraction_level, parent_context
        )

        return abstracted_summary

    def _filter_by_abstraction_level(
        self, results: list[ChildWorkflowResult], level: AbstractionLevel
    ) -> list[dict[str, Any]]:
        """Filter results based on abstraction level requirements"""

        filter_config = self.abstraction_filters[level]
        filtered_results = []

        for result in results:
            filtered_result = {
                "workflow_id": result.workflow_id,
                "agent_role": result.agent_role,
                "task_description": result.task_description,
                "completion_status": result.completion_status,
            }

            # Include information types appropriate for this level
            if InformationType.STRATEGIC_DECISIONS in filter_config.included_types:
                filtered_result["key_decisions"] = result.key_decisions[
                    :3
                ]  # Top 3 only

            if InformationType.TECHNICAL_ARCHITECTURE in filter_config.included_types:
                # Summarize technical details, don't include raw implementation
                filtered_result[
                    "architecture_summary"
                ] = self._summarize_technical_details(
                    result.technical_details, filter_config.max_detail_length
                )

            if InformationType.RISKS_BLOCKERS in filter_config.included_types:
                filtered_result["risks_identified"] = result.risks_identified

            if InformationType.DEPENDENCIES in filter_config.included_types:
                filtered_result["dependencies_created"] = result.dependencies_created

            if InformationType.RESOURCE_USAGE in filter_config.included_types:
                filtered_result["resource_impact"] = self._summarize_resource_usage(
                    result.resource_usage
                )

            if InformationType.ERROR_REPORTS in filter_config.included_types:
                # Only include if current level needs implementation details
                filtered_result["deliverables"] = result.deliverables

            filtered_results.append(filtered_result)

        return filtered_results

    def _extract_critical_information(
        self, filtered_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Extract information that MUST bubble up regardless of abstraction level"""

        critical_info = {
            "blocking_issues": [],
            "failed_workflows": [],
            "new_dependencies": [],
            "escalated_risks": [],
            "resource_constraints": [],
        }

        for result in filtered_results:
            # Always escalate failures
            if result.get("completion_status") in ["failed", "blocked"]:
                critical_info["blocking_issues"].append(
                    {
                        "workflow": result["workflow_id"],
                        "issue": result.get("completion_status"),
                        "context": result["task_description"],
                    }
                )

            # Always escalate high-impact risks
            for risk in result.get("risks_identified", []):
                if any(
                    keyword in risk.lower()
                    for keyword in ["critical", "blocking", "security", "data loss"]
                ):
                    critical_info["escalated_risks"].append(risk)

            # Always escalate new cross-workflow dependencies
            critical_info["new_dependencies"].extend(
                result.get("dependencies_created", [])
            )

        return critical_info

    async def _generate_intelligent_summary(
        self,
        filtered_results: list[dict[str, Any]],
        critical_info: dict[str, Any],
        abstraction_level: AbstractionLevel,
        parent_context: str,
    ) -> AbstractedSummary:
        """Use LLM to generate intelligent, context-aware summary"""

        filter_config = self.abstraction_filters[abstraction_level]

        system_prompt = f"""
        You are an intelligent context abstraction system. Your role is to summarize
        child workflow results for a parent workflow operating at the {abstraction_level.name} level.

        PARENT CONTEXT: {parent_context}

        ABSTRACTION REQUIREMENTS:
        - Focus on {filter_config.summary_style} perspective
        - Maximum detail length: {filter_config.max_detail_length} characters per item
        - Include only information relevant to {abstraction_level.name} level decision-making

        CRITICAL RULES:
        1. Always include critical/blocking issues regardless of abstraction level
        2. Summarize technical details appropriately for the target audience
        3. Focus on outcomes and impacts, not implementation specifics (unless technical level)
        4. Highlight dependencies and risks that affect the parent workflow
        5. Be concise but comprehensive for decision-making needs
        """

        user_message = f"""
        CHILD WORKFLOW RESULTS:
        {json.dumps(filtered_results, indent=2)}

        CRITICAL INFORMATION (must include):
        {json.dumps(critical_info, indent=2)}

        Generate an AbstractedSummary that provides the parent workflow with exactly
        the information it needs at its abstraction level, without overwhelming details.
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        response = await self.llm.ainvoke(messages)

        # Parse LLM response into structured summary
        # In production, this would use structured output or function calling
        return self._parse_llm_response_to_summary(
            response.content, filtered_results, critical_info
        )

    def _parse_llm_response_to_summary(
        self,
        llm_response: str,
        filtered_results: list[dict[str, Any]],
        critical_info: dict[str, Any],
    ) -> AbstractedSummary:
        """Parse LLM response into structured AbstractedSummary"""

        # Extract key information from LLM response
        # This is a simplified version - production would use more sophisticated parsing

        return AbstractedSummary(
            source_workflows=[r["workflow_id"] for r in filtered_results],
            executive_summary=self._extract_summary_section(
                llm_response, "executive_summary"
            ),
            key_outcomes=self._extract_list_section(llm_response, "key_outcomes"),
            critical_dependencies=critical_info.get("new_dependencies", []),
            escalated_risks=critical_info.get("escalated_risks", []),
            resource_impact=self._extract_summary_section(
                llm_response, "resource_impact"
            ),
            next_actions_required=self._extract_list_section(
                llm_response, "next_actions"
            ),
            confidence_level=self._calculate_confidence_level(filtered_results),
        )

    def _summarize_technical_details(
        self, technical_details: dict[str, Any], max_length: int
    ) -> str:
        """Summarize technical details to appropriate length"""
        if not technical_details:
            return "No technical details provided"

        # Extract most important technical decisions
        summary_parts = []
        for key, value in technical_details.items():
            if key in ["architecture", "technology_stack", "design_patterns"]:
                summary_parts.append(f"{key}: {str(value)[:100]}")

        full_summary = "; ".join(summary_parts)
        return (
            full_summary[:max_length] + "..."
            if len(full_summary) > max_length
            else full_summary
        )

    def _summarize_resource_usage(self, resource_usage: dict[str, Any]) -> str:
        """Summarize resource usage for parent-level consumption"""
        if not resource_usage:
            return "No resource impact"

        # Focus on high-level resource implications
        cpu_usage = resource_usage.get("cpu_time", 0)
        memory_usage = resource_usage.get("memory_mb", 0)

        if cpu_usage > 300 or memory_usage > 1000:  # High usage thresholds
            return f"High resource usage detected: {cpu_usage}s CPU, {memory_usage}MB memory"
        else:
            return "Normal resource usage"

    def _extract_summary_section(self, text: str, section: str) -> str:
        """Extract specific section from LLM response"""
        # Simplified extraction - production would use more robust parsing
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if section.lower() in line.lower():
                return lines[i + 1] if i + 1 < len(lines) else ""
        return "Summary not available"

    def _extract_list_section(self, text: str, section: str) -> list[str]:
        """Extract list section from LLM response"""
        # Simplified extraction - production would use more robust parsing
        items = []
        lines = text.split("\n")
        in_section = False

        for line in lines:
            if section.lower() in line.lower():
                in_section = True
                continue
            elif in_section and line.strip().startswith("-"):
                items.append(line.strip()[1:].strip())
            elif in_section and not line.strip():
                break

        return items

    def _calculate_confidence_level(
        self, filtered_results: list[dict[str, Any]]
    ) -> float:
        """Calculate confidence level based on completion status of child workflows"""
        if not filtered_results:
            return 0.0

        completed = sum(
            1 for r in filtered_results if r.get("completion_status") == "completed"
        )
        total = len(filtered_results)

        return completed / total


class ParentNodeContextManager:
    """
    Integration class for parent nodes to use context abstraction
    in their workflow processing
    """

    def __init__(self, abstraction_level: AbstractionLevel, parent_context: str):
        self.abstraction_level = abstraction_level
        self.parent_context = parent_context
        self.abstraction_engine = ContextAbstractionEngine()

    async def process_child_results(
        self, child_results: list[ChildWorkflowResult]
    ) -> AbstractedSummary:
        """Main method for parent nodes to get filtered child results"""

        return await self.abstraction_engine.abstract_child_results(
            child_results=child_results,
            parent_abstraction_level=self.abstraction_level,
            parent_context=self.parent_context,
        )

    def should_escalate_to_parent(self, summary: AbstractedSummary) -> bool:
        """Determine if results should be escalated to the next parent level"""

        # Always escalate if there are blocking issues
        if summary.escalated_risks or summary.confidence_level < 0.8:
            return True

        # Escalate based on abstraction level requirements
        if self.abstraction_level == AbstractionLevel.TECHNICAL:
            # Technical level only escalates critical issues
            return len(summary.escalated_risks) > 0

        return False


# Usage example for integration with OAMAT workflow nodes
async def example_parent_node_usage():
    """Example of how parent nodes would use the context abstraction system"""

    # Parent node receives results from multiple child workflows
    child_results = [
        ChildWorkflowResult(
            workflow_id="auth_workflow_001",
            agent_role="security_engineer",
            task_description="Implement user authentication system",
            completion_status="completed",
            key_decisions=[
                "JWT tokens",
                "OAuth2 integration",
                "Password hashing with bcrypt",
            ],
            technical_details={
                "technology_stack": "FastAPI, JWT, bcrypt, Redis",
                "architecture": "Microservice with token validation middleware",
                "security_measures": "Rate limiting, input validation, secure headers",
            },
            dependencies_created=["Redis session store", "User database schema"],
            risks_identified=["Token expiration handling needs monitoring"],
            deliverables=["Auth API", "Login UI", "Security middleware"],
        )
        # ... more child results
    ]

    # Parent at managerial level processes results
    context_manager = ParentNodeContextManager(
        abstraction_level=AbstractionLevel.MANAGERIAL,
        parent_context="Building e-commerce platform - coordinating core services",
    )

    # Get abstracted summary appropriate for managerial level
    abstracted_summary = await context_manager.process_child_results(child_results)

    # Check if issues need escalation to executive level
    needs_escalation = context_manager.should_escalate_to_parent(abstracted_summary)

    return abstracted_summary, needs_escalation
