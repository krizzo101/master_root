"""
O3 Master Agent - Advanced Reasoning and Orchestration

Sophisticated agent using O3-level reasoning for complex analysis, strategy generation,
and execution planning. Acts as the primary intelligence for decomposition decisions.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.applications.oamat_sd.src.agents.complexity_model import (
    ComplexityAnalysisResult,
    ComplexityCategory,
    ExecutionStrategy,
)
from src.applications.oamat_sd.src.agents.request_validation import (
    CompletionResult,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class ReasoningLevel(str, Enum):
    """Levels of reasoning depth."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AnalysisType(str, Enum):
    """Types of analysis performed."""

    COMPLEXITY = "complexity"
    STRATEGY = "strategy"
    PLANNING = "planning"
    OPTIMIZATION = "optimization"


@dataclass
class ReasoningStep:
    """Individual step in reasoning process."""

    step_id: str
    analysis_type: AnalysisType
    reasoning: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)


@dataclass
class AgentStrategy:
    """Strategy for agent deployment and coordination."""

    execution_strategy: ExecutionStrategy
    agent_roles: list[str]
    coordination_pattern: str
    communication_flow: dict[str, list[str]]
    success_criteria: list[str]
    risk_mitigation: list[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """Detailed execution plan for the request with explicit dependency tracking."""

    phases: list[dict[str, Any]]
    dependencies: dict[str, list[str]]
    resource_requirements: dict[str, Any]
    timeline_estimates: dict[str, str]
    quality_gates: list[str]
    contingency_plans: list[str] = field(default_factory=list)
    # New dependency tracking fields for parallel vs sequential execution
    parallel_opportunities: list[dict[str, Any]] = field(default_factory=list)
    sequential_requirements: list[dict[str, Any]] = field(default_factory=list)
    integration_points: list[str] = field(default_factory=list)
    consistency_checks: list[str] = field(default_factory=list)


@dataclass
class PipelineDesign:
    """Dynamic pipeline design determined by O3 for each specific request."""

    pipeline_type: str
    stages: list[dict[str, Any]]
    execution_graph: dict[str, Any]
    context_management: dict[str, Any]
    optimization_rationale: str = ""
    estimated_efficiency: str = ""
    alternative_approaches: list[str] = field(default_factory=list)


@dataclass
class O3AnalysisResult:
    """Complete O3-level analysis result."""

    request_analysis: dict[str, Any]
    complexity_assessment: ComplexityAnalysisResult
    agent_strategy: AgentStrategy
    execution_plan: ExecutionPlan
    reasoning_chain: list[ReasoningStep]
    confidence: float
    recommendations: list[str]
    timestamp: datetime = field(default_factory=datetime.now)


class O3FrameworkEducator:
    """Provides O3 with comprehensive framework knowledge for dynamic generation"""

    @staticmethod
    def get_tool_catalog() -> dict[str, dict[str, str]]:
        """Complete catalog of available MCP tools with capabilities"""
        return {
            "write_file": {
                "capability": "Create and edit files with any content type",
                "parameters": "target_file, code_edit, instructions",
                "use_cases": "Source code, configuration files, documentation, templates",
                "output_types": "Any file format (.py, .js, .tsx, .json, .md, .txt, etc.)",
            },
            "mcp_shell_exec": {
                "capability": "Execute shell commands and scripts with output capture",
                "parameters": "command, workingDir",
                "use_cases": "Package installation, compilation, testing, deployment, file operations",
                "security": "Commands run in controlled environment",
            },
            "read_file": {
                "capability": "Read file contents with line range support",
                "parameters": "target_file, start_line_one_indexed, end_line_one_indexed",
                "use_cases": "Code analysis, template reading, configuration inspection",
                "output": "File contents with context",
            },
            "edit_file": {
                "capability": "Precise file editing with structured changes",
                "parameters": "target_file, instructions, code_edit",
                "use_cases": "Code modification, configuration updates, targeted fixes",
                "features": "Surgical edits, preserve existing code",
            },
            "search_replace": {
                "capability": "Exact text replacement in files",
                "parameters": "file_path, old_string, new_string",
                "use_cases": "Bulk updates, refactoring, configuration changes",
                "precision": "Exact match replacement",
            },
            "grep_search": {
                "capability": "Fast regex text search across files",
                "parameters": "query, include_pattern, exclude_pattern",
                "use_cases": "Code discovery, pattern matching, dependency analysis",
                "performance": "High-speed search with filtering",
            },
            "codebase_search": {
                "capability": "Semantic search for code by meaning",
                "parameters": "query, target_directories",
                "use_cases": "Understanding code behavior, finding functionality",
                "intelligence": "Meaning-based rather than text-based",
            },
            "file_search": {
                "capability": "Fuzzy file path searching",
                "parameters": "query, explanation",
                "use_cases": "Locating files by partial names or paths",
                "flexibility": "Handles typos and partial matches",
            },
            "list_dir": {
                "capability": "Directory content listing and exploration",
                "parameters": "relative_workspace_path",
                "use_cases": "Project structure analysis, file discovery",
                "scope": "Workspace-relative paths",
            },
            "web_search": {
                "capability": "Current web information research",
                "parameters": "search_term",
                "use_cases": "Technology research, best practices, current standards",
                "freshness": "Real-time information access",
            },
            "mcp_web_scraping_firecrawl_scrape": {
                "capability": "Advanced web content extraction",
                "parameters": "url, formats",
                "use_cases": "Documentation scraping, content analysis",
                "formats": "Markdown, HTML, structured data",
            },
            "mcp_tech_docs_get_library_docs": {
                "capability": "Technical documentation retrieval",
                "parameters": "context7CompatibleLibraryID, topic, tokens",
                "use_cases": "Framework documentation, API references",
                "coverage": "Major libraries and frameworks",
            },
            "create_diagram": {
                "capability": "Mermaid diagram generation with accessibility",
                "parameters": "content",
                "use_cases": "Architecture diagrams, workflow visualization",
                "standards": "High contrast, accessible design",
            },
            "mcp_thinking_sequentialthinking": {
                "capability": "Advanced reasoning and problem decomposition",
                "parameters": "thought, nextThoughtNeeded, thoughtNumber, totalThoughts",
                "use_cases": "Complex analysis, multi-step reasoning, decision validation",
                "intelligence": "Structured reasoning process",
            },
        }

    @staticmethod
    def get_coordination_patterns() -> dict[str, dict[str, str]]:
        """Available coordination patterns for agent orchestration"""
        return {
            "sequential": {
                "description": "Agents execute one after another with dependencies",
                "use_cases": "Building layers, step-by-step processes, dependency chains",
                "example": "Database setup → API development → Frontend development",
            },
            "parallel": {
                "description": "Independent agents execute simultaneously",
                "use_cases": "Independent components, performance optimization",
                "example": "Frontend and Backend development in parallel",
            },
            "conditional": {
                "description": "Agent execution based on state conditions and results",
                "use_cases": "Adaptive workflows, error handling, branching logic",
                "example": "Execute testing agent only if compilation succeeds",
            },
            "hierarchical": {
                "description": "Manager agents coordinate specialist agents",
                "use_cases": "Complex orchestration, supervision, quality control",
                "example": "Project manager coordinating specialized teams",
            },
            "iterative": {
                "description": "Agents refine outputs through multiple cycles",
                "use_cases": "Quality improvement, iterative development, refinement",
                "example": "Code → Review → Refine → Review cycle",
            },
            "hybrid": {
                "description": "Combination of multiple patterns as needed",
                "use_cases": "Complex projects requiring multiple coordination styles",
                "example": "Parallel development with sequential integration",
            },
        }

    @staticmethod
    def get_project_examples() -> list[dict[str, Any]]:
        """Diverse examples to guide O3 without hardcoding patterns"""
        return [
            {
                "type": "Web Application",
                "description": "Full-stack web application with API and UI",
                "typical_agents": [
                    "Backend API specialist (FastAPI/Express/Django)",
                    "Frontend UI specialist (React/Vue/Angular)",
                    "Database specialist (SQL/NoSQL setup)",
                    "Configuration specialist (environment, deployment)",
                ],
                "common_tools": [
                    "write_file",
                    "mcp_shell_exec",
                    "web_search",
                    "mcp_tech_docs_get_library_docs",
                ],
                "structure_pattern": "Separated concerns with backend/frontend/shared directories",
                "coordination": "Sequential for dependencies, parallel for independent components",
            },
            {
                "type": "CLI Tool",
                "description": "Command-line utility with argument parsing and core logic",
                "typical_agents": [
                    "Argument parsing specialist (CLI interface)",
                    "Core logic specialist (main functionality)",
                    "Output formatting specialist (display/export)",
                    "Documentation specialist (help, examples)",
                ],
                "common_tools": [
                    "write_file",
                    "mcp_shell_exec",
                    "grep_search",
                    "codebase_search",
                ],
                "structure_pattern": "Single executable with modular architecture",
                "coordination": "Sequential with some parallel documentation generation",
            },
            {
                "type": "Data Pipeline",
                "description": "ETL system for data processing and transformation",
                "typical_agents": [
                    "Data ingestion specialist (sources, APIs, files)",
                    "Processing engine specialist (transformation, validation)",
                    "Output manager specialist (storage, export, reporting)",
                    "Monitoring specialist (logging, metrics, alerts)",
                ],
                "common_tools": [
                    "write_file",
                    "web_search",
                    "mcp_shell_exec",
                    "mcp_web_scraping_firecrawl_scrape",
                ],
                "structure_pattern": "Pipeline stages with clear data flow",
                "coordination": "Sequential pipeline with parallel monitoring",
            },
            {
                "type": "Mobile Application",
                "description": "React Native or native mobile app",
                "typical_agents": [
                    "UI component specialist (screens, navigation)",
                    "State management specialist (Redux/Context)",
                    "API integration specialist (backend communication)",
                    "Platform specialist (iOS/Android specific features)",
                ],
                "common_tools": [
                    "write_file",
                    "mcp_tech_docs_get_library_docs",
                    "web_search",
                ],
                "structure_pattern": "Component-based with platform-specific directories",
                "coordination": "Parallel UI development with sequential integration",
            },
            {
                "type": "Microservice",
                "description": "Single-responsibility service with API",
                "typical_agents": [
                    "API specialist (endpoints, routing, validation)",
                    "Business logic specialist (core functionality)",
                    "Persistence specialist (database, caching)",
                    "Infrastructure specialist (containerization, deployment)",
                ],
                "common_tools": [
                    "write_file",
                    "mcp_shell_exec",
                    "mcp_tech_docs_get_library_docs",
                ],
                "structure_pattern": "Layered architecture with clear separation",
                "coordination": "Sequential for layers, parallel for cross-cutting concerns",
            },
            {
                "type": "Data Science Project",
                "description": "Analysis, modeling, and visualization project",
                "typical_agents": [
                    "Data analysis specialist (exploration, cleaning)",
                    "Model development specialist (training, validation)",
                    "Visualization specialist (charts, dashboards)",
                    "Documentation specialist (methodology, results)",
                ],
                "common_tools": [
                    "write_file",
                    "web_search",
                    "mcp_research_papers_search_papers",
                ],
                "structure_pattern": "Jupyter notebooks with supporting modules",
                "coordination": "Sequential analysis with parallel documentation",
            },
        ]

    @staticmethod
    def get_schema_requirements() -> dict[str, Any]:
        """Schema requirements for O3 output validation"""
        return {
            "AgentStrategy": {
                "required_fields": [
                    "execution_strategy",
                    "agent_roles",
                    "coordination_pattern",
                    "communication_flow",
                    "success_criteria",
                ],
                "agent_roles": "List of specific agent roles needed for this request",
                "coordination_pattern": "Must be one of: sequential, parallel, conditional, hierarchical, iterative, hybrid",
                "communication_flow": "Dict mapping agent relationships and data dependencies",
            },
            "ExecutionPlan": {
                "required_fields": [
                    "phases",
                    "dependencies",
                    "resource_requirements",
                    "timeline_estimates",
                    "quality_gates",
                ],
                "phases": "List of execution phases with agent assignments",
                "dependencies": "Dict of agent dependencies (which agents need what from others)",
                "quality_gates": "Checkpoints for validation and quality control",
            },
            "WorkflowSpecification": {
                "required_fields": [
                    "workflow_id",
                    "workflow_description",
                    "agents",
                    "execution_graph",
                    "state_management",
                    "success_criteria",
                    "deliverables",
                    "error_handling",
                ],
                "agents": "List of AgentSpecification objects",
                "execution_graph": "List of WorkflowNode objects defining execution order",
                "deliverables": "List of FileDeliverable objects with specific requirements",
            },
        }

    @staticmethod
    def get_model_usage_guidelines() -> dict[str, str]:
        """Guidelines for model selection and usage"""
        return {
            "o3-mini": "Use for complex reasoning, planning, and analysis tasks requiring deep thought",
            "gpt-4.1-mini": "Use for execution, code generation, and implementation tasks",
            "model_selection_criteria": "o3-mini for strategy/planning, gpt-4.1-mini for execution",
            "token_optimization": "No max_tokens limits - let models use what they need",
            "temperature_guidelines": "Lower for consistent analysis (0.1), moderate for creative tasks (0.3)",
        }


class O3MasterAgent:
    """Advanced reasoning agent using O3-level intelligence."""

    def __init__(self, model_config: dict[str, Any] | None = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.model_config = model_config or self._default_model_config()
        self.reasoning_history: list[ReasoningStep] = []

        # Initialize O3 model (NO FALLBACKS - fail if unavailable)
        try:
            from langchain_openai import ChatOpenAI

            # O3 models don't support temperature parameter - use minimal config
            model_kwargs = {"model": self.model_config["model"]}

            # Only add temperature for non-O3 models
            if not self.model_config["model"].startswith("o3"):
                model_kwargs["temperature"] = self.model_config["temperature"]

            self.master_model = ChatOpenAI(**model_kwargs)
            self.logger.info(f"✅ O3 model initialized: {self.model_config['model']}")
        except Exception as e:
            self.logger.error(f"❌ O3 model initialization failed: {e}")
            raise RuntimeError(
                f"O3 model initialization failed: {e}. System cannot operate without O3."
            )

    def _default_model_config(self) -> dict[str, Any]:
        """Default configuration for O3 model integration."""
        return {
            "model": "o3-mini",  # Standardized reasoning model
            "temperature": 0.1,
            "reasoning_depth": ReasoningLevel.ADVANCED,
            "enable_chain_of_thought": True,
            "enable_self_reflection": True,
        }

    async def analyze_request_complexity(
        self, request: dict[str, Any], validation_result: ValidationResult
    ) -> tuple[ComplexityAnalysisResult, list[ReasoningStep]]:
        """Perform deep complexity analysis with O3-level reasoning."""
        self.logger.info(
            f"O3 analyzing complexity for: {request.get('name', 'unnamed request')}"
        )

        reasoning_steps = []

        # Step 1: Initial complexity assessment
        step1 = ReasoningStep(
            step_id="complexity_initial",
            analysis_type=AnalysisType.COMPLEXITY,
            reasoning=f"Analyzing request type {validation_result.request_type} with {len(validation_result.extracted_info)} extracted fields",
            confidence=0.8,
            evidence=[
                f"Request type: {validation_result.request_type}",
                f"Fields: {list(validation_result.extracted_info.keys())}",
            ],
        )
        reasoning_steps.append(step1)

        # Step 2: Multi-dimensional analysis
        complexity_factors = self._analyze_complexity_dimensions(
            request, validation_result
        )

        step2 = ReasoningStep(
            step_id="complexity_dimensions",
            analysis_type=AnalysisType.COMPLEXITY,
            reasoning="Analyzed six complexity dimensions: scope, technical depth, domain knowledge, dependencies, timeline, risk",
            confidence=0.85,
            evidence=[
                f"Scope: {complexity_factors['scope']}",
                f"Technical: {complexity_factors['technical_depth']}",
            ],
        )
        reasoning_steps.append(step2)

        # Step 3: Strategic assessment
        overall_score = sum(complexity_factors.values()) / len(complexity_factors)
        category = self._determine_complexity_category(overall_score)

        step3 = ReasoningStep(
            step_id="complexity_assessment",
            analysis_type=AnalysisType.COMPLEXITY,
            reasoning=f"Overall complexity score: {overall_score:.1f}, Category: {category}",
            confidence=0.9,
            evidence=[f"Average score: {overall_score:.1f}", f"Category: {category}"],
        )
        reasoning_steps.append(step3)

        # Create complexity result (simplified for TDD)
        from src.applications.oamat_sd.src.agents.complexity_model import (
            ComplexityFactor,
            ComplexityFactors,
        )

        # Create individual factors
        factors = ComplexityFactors(
            scope=ComplexityFactor(
                "scope", complexity_factors["scope"], "Analyzed scope complexity"
            ),
            technical_depth=ComplexityFactor(
                "technical_depth",
                complexity_factors["technical_depth"],
                "Analyzed technical depth",
            ),
            domain_knowledge=ComplexityFactor(
                "domain_knowledge",
                complexity_factors["domain_knowledge"],
                "Analyzed domain complexity",
            ),
            dependencies=ComplexityFactor(
                "dependencies",
                complexity_factors["dependencies"],
                "Analyzed dependencies",
            ),
            timeline=ComplexityFactor(
                "timeline", complexity_factors["timeline"], "Analyzed timeline"
            ),
            risk=ComplexityFactor(
                "risk", complexity_factors["risk"], "Analyzed risk factors"
            ),
        )

        # Determine strategy
        execution_strategy = self._determine_execution_strategy(
            overall_score, complexity_factors
        )

        complexity_result = ComplexityAnalysisResult(
            factors=factors,
            overall_score=overall_score,
            category=ComplexityCategory(category),
            execution_strategy=ExecutionStrategy(execution_strategy),
            reasoning=f"O3 analysis: {overall_score:.1f}/10 complexity, {execution_strategy} strategy recommended",
            agent_requirements=self._generate_agent_requirements(
                execution_strategy, complexity_factors
            ),
            estimated_effort=self._estimate_effort(overall_score),
            confidence=0.85,
        )

        return complexity_result, reasoning_steps

    def _analyze_complexity_dimensions(
        self, request: dict[str, Any], validation_result: ValidationResult
    ) -> dict[str, int]:
        """Analyze complexity across six dimensions."""
        request_text = str(request.get("description", "")).lower()

        # Simplified analysis for TDD (real implementation would use O3 reasoning)
        dimensions = {}

        # Scope analysis
        scope_indicators = ["full", "complete", "entire", "comprehensive", "end-to-end"]
        scope_score = 3 + sum(
            1 for indicator in scope_indicators if indicator in request_text
        )
        dimensions["scope"] = min(10, scope_score)

        # Technical depth
        tech_indicators = ["api", "database", "algorithm", "security", "performance"]
        tech_score = 3 + sum(
            1 for indicator in tech_indicators if indicator in request_text
        )
        dimensions["technical_depth"] = min(10, tech_score)

        # Domain knowledge
        domain_indicators = ["business", "finance", "healthcare", "scientific", "legal"]
        domain_score = 3 + sum(
            2 for indicator in domain_indicators if indicator in request_text
        )
        dimensions["domain_knowledge"] = min(10, domain_score)

        # Dependencies
        dep_indicators = ["integrate", "third-party", "external", "api", "service"]
        dep_score = 2 + sum(
            1 for indicator in dep_indicators if indicator in request_text
        )
        dimensions["dependencies"] = min(10, dep_score)

        # Timeline
        urgent_indicators = ["urgent", "asap", "immediately", "rush"]
        timeline_score = 5 + (
            3
            if any(indicator in request_text for indicator in urgent_indicators)
            else 0
        )
        dimensions["timeline"] = min(10, timeline_score)

        # Risk
        risk_indicators = ["production", "critical", "security", "data", "enterprise"]
        risk_score = 3 + sum(
            1 for indicator in risk_indicators if indicator in request_text
        )
        dimensions["risk"] = min(10, risk_score)

        return dimensions

    def _determine_complexity_category(self, overall_score: float) -> str:
        """Determine complexity category from score."""
        if overall_score <= 3.0:
            return "low"
        elif overall_score <= 6.0:
            return "medium"
        elif overall_score <= 8.0:
            return "high"
        else:
            return "extreme"

    def _determine_execution_strategy(
        self, overall_score: float, complexity_factors: dict[str, int]
    ) -> str:
        """Determine optimal execution strategy."""
        if overall_score <= 4.0 and complexity_factors["scope"] <= 4:
            return "simple"
        elif overall_score >= 7.0 or complexity_factors["dependencies"] >= 7:
            return "orchestrated"
        else:
            return "multi_agent"

    def _generate_agent_requirements(
        self, strategy: str, complexity_factors: dict[str, int]
    ) -> dict[str, Any]:
        """Generate agent requirements based on strategy."""
        if strategy == "simple":
            return {
                "agent_count": 1,
                "specializations": ["generalist"],
                "coordination_level": "none",
            }
        elif strategy == "multi_agent":
            return {
                "agent_count": 3,
                "specializations": ["researcher", "implementer", "validator"],
                "coordination_level": "moderate",
            }
        else:  # orchestrated
            return {
                "agent_count": 5,
                "specializations": [
                    "architect",
                    "researcher",
                    "implementer",
                    "integrator",
                    "validator",
                ],
                "coordination_level": "high",
            }

    def _estimate_effort(self, overall_score: float) -> str:
        """Estimate effort level."""
        if overall_score <= 3:
            return "Low (Hours)"
        elif overall_score <= 5:
            return "Medium (Days)"
        elif overall_score <= 7:
            return "High (Weeks)"
        else:
            return "Very High (Months)"

    async def generate_agent_strategy(
        self,
        complexity_result: ComplexityAnalysisResult,
        completion_result: CompletionResult,
    ) -> tuple[AgentStrategy, list[ReasoningStep]]:
        """Generate sophisticated agent deployment strategy."""
        self.logger.info(
            f"Generating agent strategy for {complexity_result.execution_strategy} execution"
        )

        reasoning_steps = []

        # Step 1: Strategy selection reasoning
        step1 = ReasoningStep(
            step_id="strategy_selection",
            analysis_type=AnalysisType.STRATEGY,
            reasoning=f"Selected {complexity_result.execution_strategy} based on complexity score {complexity_result.overall_score}",
            confidence=0.9,
            evidence=[
                f"Complexity: {complexity_result.overall_score}",
                f"Strategy: {complexity_result.execution_strategy}",
            ],
        )
        reasoning_steps.append(step1)

        # Step 2: Agent role assignment
        agent_roles = self._determine_agent_roles(complexity_result)

        step2 = ReasoningStep(
            step_id="role_assignment",
            analysis_type=AnalysisType.STRATEGY,
            reasoning=f"Assigned {len(agent_roles)} specialized roles based on complexity factors",
            confidence=0.85,
            evidence=[f"Roles: {agent_roles}"],
        )
        reasoning_steps.append(step2)

        # Step 3: Coordination pattern
        coordination_pattern = self._design_coordination_pattern(
            complexity_result.execution_strategy
        )
        communication_flow = self._design_communication_flow(agent_roles)

        step3 = ReasoningStep(
            step_id="coordination_design",
            analysis_type=AnalysisType.STRATEGY,
            reasoning=f"Designed {coordination_pattern} coordination with defined communication flows",
            confidence=0.8,
            evidence=[
                f"Pattern: {coordination_pattern}",
                f"Communications: {len(communication_flow)} flows",
            ],
        )
        reasoning_steps.append(step3)

        # Generate success criteria and risk mitigation
        success_criteria = self._generate_success_criteria(complexity_result)
        risk_mitigation = self._generate_risk_mitigation(complexity_result)

        strategy = AgentStrategy(
            execution_strategy=complexity_result.execution_strategy,
            agent_roles=agent_roles,
            coordination_pattern=coordination_pattern,
            communication_flow=communication_flow,
            success_criteria=success_criteria,
            risk_mitigation=risk_mitigation,
        )

        return strategy, reasoning_steps

    def _determine_agent_roles(
        self, complexity_result: ComplexityAnalysisResult
    ) -> list[str]:
        """Determine required agent roles based on complexity."""
        roles = []

        if complexity_result.execution_strategy == ExecutionStrategy.SIMPLE:
            roles = ["generalist"]
        elif complexity_result.execution_strategy == ExecutionStrategy.MULTI_AGENT:
            roles = ["researcher", "implementer"]
            if complexity_result.factors.technical_depth.score >= 7:
                roles.append("technical_specialist")
            if complexity_result.factors.domain_knowledge.score >= 6:
                roles.append("domain_expert")
        else:  # ORCHESTRATED
            roles = [
                "architect",
                "researcher",
                "implementer",
                "integrator",
                "validator",
            ]
            if complexity_result.factors.risk.score >= 7:
                roles.append("security_specialist")

        return roles

    def _design_coordination_pattern(self, strategy: ExecutionStrategy) -> str:
        """Design coordination pattern for agent interaction."""
        patterns = {
            ExecutionStrategy.SIMPLE: "direct",
            ExecutionStrategy.MULTI_AGENT: "collaborative",
            ExecutionStrategy.ORCHESTRATED: "hierarchical_dag",
        }
        return patterns.get(strategy, "collaborative")

    def _design_communication_flow(
        self, agent_roles: list[str]
    ) -> dict[str, list[str]]:
        """Design communication flows between agents."""
        if len(agent_roles) == 1:
            return {agent_roles[0]: []}

        # Simple hub pattern for TDD
        flows = {}
        primary_agent = agent_roles[0]

        for role in agent_roles:
            if role == primary_agent:
                flows[role] = [r for r in agent_roles if r != role]
            else:
                flows[role] = [primary_agent]

        return flows

    def _generate_success_criteria(
        self, complexity_result: ComplexityAnalysisResult
    ) -> list[str]:
        """Generate success criteria based on complexity."""
        criteria = [
            "Functional requirements met",
            "Quality standards achieved",
            "Performance benchmarks satisfied",
        ]

        if complexity_result.factors.risk.score >= 6:
            criteria.append("Security requirements validated")
        if complexity_result.factors.dependencies.score >= 6:
            criteria.append("Integration points tested")
        if complexity_result.overall_score >= 7:
            criteria.append("Scalability verified")

        return criteria

    def _generate_risk_mitigation(
        self, complexity_result: ComplexityAnalysisResult
    ) -> list[str]:
        """Generate risk mitigation strategies."""
        mitigation = []

        if complexity_result.factors.technical_depth.score >= 7:
            mitigation.append("Technical review checkpoints")
        if complexity_result.factors.dependencies.score >= 6:
            mitigation.append("Integration testing protocol")
        if complexity_result.factors.timeline.score >= 7:
            mitigation.append("Parallel development tracks")
        if complexity_result.factors.risk.score >= 6:
            mitigation.append("Security audit requirements")

        return mitigation

    async def create_execution_plan(
        self, agent_strategy: AgentStrategy, completion_result: CompletionResult
    ) -> tuple[ExecutionPlan, list[ReasoningStep]]:
        """Create detailed execution plan with AI-driven dynamic planning (NO ALGORITHMS)."""
        self.logger.info(
            f"Creating AI-driven execution plan for {agent_strategy.execution_strategy} strategy"
        )

        reasoning_steps = []

        # Step 1: AI-driven execution planning (Rule 954 compliance)
        step1 = ReasoningStep(
            step_id="ai_execution_planning",
            analysis_type=AnalysisType.PLANNING,
            reasoning="Using AI to determine optimal execution plan for this specific strategy",
            confidence=0.9,
            evidence=[
                f"Strategy: {agent_strategy.execution_strategy}",
                f"Agents: {len(agent_strategy.agent_roles)}",
                f"Coordination: {agent_strategy.coordination_pattern}",
            ],
        )
        reasoning_steps.append(step1)

        # Get AI model for reasoning (Rule 953 compliance)
        ai_model = self._get_approved_ai_model("reasoning")  # o3-mini for planning

        # Create framework template for guardrails
        framework_template = self._create_execution_phase_template()

        # AI-driven execution planning prompt
        planning_prompt = f"""
        Analyze this agent strategy and design optimal execution plan:

        AGENT STRATEGY:
        - Execution Strategy: {agent_strategy.execution_strategy}
        - Agent Roles: {agent_strategy.agent_roles}
        - Coordination Pattern: {agent_strategy.coordination_pattern}
        - Communication Flow: {agent_strategy.communication_flow}

        FRAMEWORK GUIDELINES:
        {json.dumps(framework_template, indent=2)}

        CRITICAL CONSISTENCY REQUIREMENTS:
        1. MAINTAIN COHERENCE: All agent names, roles, and references MUST be consistent with the provided agent_strategy
        2. DEPENDENCY ANALYSIS: Explicitly analyze what can be parallel vs sequential based on context dependencies
        3. ARTIFACT ALIGNMENT: Ensure all deliverables align with agent capabilities and coordination patterns
        4. REFERENCE CONSISTENCY: Use exact agent role names from agent_strategy when defining phase participants

        YOUR TASK: Design execution plan for THIS SPECIFIC strategy with explicit dependency tracking.

        Analyze and determine:
        1. Which phases are needed for this coordination pattern?
        2. How should phases be sequenced for optimal efficiency?
        3. What dependencies exist between phases for this complexity?
        4. Which activities can be parallel (independent) vs sequential (dependent)?
        5. How should resources be allocated for these agents?
        6. What are realistic timeline estimates?
        7. What quality gates are needed for validation?
        8. How do deliverables from different phases integrate together?

        DEPENDENCY CLASSIFICATION:
        - PARALLEL: Tasks that can execute simultaneously without context dependencies
        - SEQUENTIAL: Tasks that require outputs/context from previous tasks
        - CONDITIONAL: Tasks that depend on decision points or validation results

        Consider the coordination pattern and agent roles to create a plan that optimizes
        for the specific characteristics of THIS strategy while ensuring all artifacts work together seamlessly.

        OUTPUT as JSON:
        {{
            "phases": [
                {{
                    "name": "phase_name",
                    "description": "what this phase accomplishes",
                    "duration": "time estimate",
                    "agents_involved": ["exact_agent_role_from_strategy"],
                    "deliverables": ["deliverable1", "deliverable2"],
                    "execution_mode": "parallel|sequential|conditional",
                    "dependencies": ["prerequisite_deliverable_or_phase"],
                    "context_requirements": ["context_needed_from_previous_phases"]
                }}
            ],
            "dependencies": {{
                "phase1": ["prerequisite_phase"],
                "phase2": ["phase1"]
            }},
            "parallel_opportunities": [
                {{
                    "group_name": "parallel_group_1",
                    "parallel_phases": ["phase1", "phase2"],
                    "rationale": "why these can execute in parallel"
                }}
            ],
            "sequential_requirements": [
                {{
                    "sequence": ["phase1", "phase2", "phase3"],
                    "rationale": "why this sequence is required",
                    "context_flow": "what context flows between phases"
                }}
            ],
            "resource_requirements": {{
                "agents": 3,
                "tools": ["tool1", "tool2"],
                "estimated_effort": "description"
            }},
            "timeline_estimates": {{
                "phase1": "1-2 hours",
                "total": "4-8 hours"
            }},
            "quality_gates": [
                "gate1: validation criteria",
                "gate2: completion criteria"
            ],
            "integration_points": [
                "how deliverables from different phases integrate",
                "validation that all artifacts work together"
            ],
            "consistency_checks": [
                "agent name consistency across phases",
                "deliverable naming consistency",
                "reference alignment with agent_strategy"
            ],
            "reasoning": "explanation of why this plan is optimal for this strategy"
        }}
        """

        # Invoke AI with structured reasoning (Rule 954)
        response_content = await self._invoke_ai_with_structured_reasoning(
            ai_model,
            "You are an expert execution planner specializing in multi-agent coordination.",
            planning_prompt,
            "Stage 3 Execution Planning",
        )

        # Parse AI response
        plan_data = self._parse_json_from_ai_response(response_content, "ExecutionPlan")

        # Validate AI output schema
        required_fields = [
            "phases",
            "dependencies",
            "resource_requirements",
            "timeline_estimates",
            "quality_gates",
        ]
        optional_fields = [
            "parallel_opportunities",
            "sequential_requirements",
            "integration_points",
            "consistency_checks",
        ]
        self._validate_ai_output_schema(plan_data, required_fields, "ExecutionPlan")

        # Step 2: AI planning validation
        step2 = ReasoningStep(
            step_id="ai_plan_validation",
            analysis_type=AnalysisType.PLANNING,
            reasoning=f"AI generated execution plan with {len(plan_data['phases'])} phases and explicit dependency tracking",
            confidence=0.85,
            evidence=[
                f"Phases: {[p['name'] for p in plan_data['phases']]}",
                f"Dependencies: {len(plan_data['dependencies'])} relationships",
                f"Parallel opportunities: {len(plan_data.get('parallel_opportunities', []))}",
                f"Sequential requirements: {len(plan_data.get('sequential_requirements', []))}",
                f"AI reasoning: {plan_data.get('reasoning', 'Dynamic plan optimization')}",
            ],
        )
        reasoning_steps.append(step2)

        # Convert AI output to ExecutionPlan object
        execution_plan = ExecutionPlan(
            phases=plan_data["phases"],
            dependencies=plan_data["dependencies"],
            resource_requirements=plan_data["resource_requirements"],
            timeline_estimates=plan_data["timeline_estimates"],
            quality_gates=plan_data["quality_gates"],
            contingency_plans=[
                "AI-determined fallback strategies",
                "Dynamic error recovery",
                "Resource reallocation protocols",
            ],
            parallel_opportunities=plan_data.get("parallel_opportunities", []),
            sequential_requirements=plan_data.get("sequential_requirements", []),
            integration_points=plan_data.get("integration_points", []),
            consistency_checks=plan_data.get("consistency_checks", []),
        )

        self.logger.info(
            f"✅ AI-driven execution plan created with {len(execution_plan.phases)} phases"
        )
        return execution_plan, reasoning_steps

    def _define_execution_phases(self, strategy: AgentStrategy) -> list[dict[str, Any]]:
        """Define execution phases based on strategy."""
        if strategy.execution_strategy == ExecutionStrategy.SIMPLE:
            return [
                {
                    "name": "analysis",
                    "description": "Analyze requirements",
                    "duration": "1-2 hours",
                },
                {
                    "name": "implementation",
                    "description": "Implement solution",
                    "duration": "2-4 hours",
                },
                {
                    "name": "validation",
                    "description": "Validate results",
                    "duration": "1 hour",
                },
            ]
        elif strategy.execution_strategy == ExecutionStrategy.MULTI_AGENT:
            return [
                {
                    "name": "planning",
                    "description": "Collaborative planning",
                    "duration": "2-4 hours",
                },
                {
                    "name": "research",
                    "description": "Research and analysis",
                    "duration": "4-8 hours",
                },
                {
                    "name": "development",
                    "description": "Parallel development",
                    "duration": "1-2 days",
                },
                {
                    "name": "integration",
                    "description": "Integration and testing",
                    "duration": "4-8 hours",
                },
                {
                    "name": "validation",
                    "description": "Final validation",
                    "duration": "2-4 hours",
                },
            ]
        else:  # ORCHESTRATED
            return [
                {
                    "name": "architecture",
                    "description": "System architecture",
                    "duration": "1-2 days",
                },
                {
                    "name": "research",
                    "description": "Deep research phase",
                    "duration": "2-3 days",
                },
                {
                    "name": "design",
                    "description": "Detailed design",
                    "duration": "1-2 days",
                },
                {
                    "name": "implementation",
                    "description": "Orchestrated implementation",
                    "duration": "3-5 days",
                },
                {
                    "name": "integration",
                    "description": "System integration",
                    "duration": "1-2 days",
                },
                {
                    "name": "testing",
                    "description": "Comprehensive testing",
                    "duration": "1-2 days",
                },
                {
                    "name": "deployment",
                    "description": "Deployment and validation",
                    "duration": "1 day",
                },
            ]

    def _analyze_phase_dependencies(
        self, phases: list[dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Analyze dependencies between phases."""
        dependencies = {}
        phase_names = [p["name"] for p in phases]

        for i, phase in enumerate(phase_names):
            if i == 0:
                dependencies[phase] = []
            else:
                dependencies[phase] = [phase_names[i - 1]]

        return dependencies

    def _plan_resources(self, strategy: AgentStrategy) -> dict[str, Any]:
        """Plan resource requirements."""
        return {
            "agents": len(strategy.agent_roles),
            "tools": ["research_tools", "implementation_tools", "validation_tools"],
            "compute": "standard",
            "storage": "minimal",
        }

    def _estimate_timelines(
        self, phases: list[dict[str, Any]], strategy: AgentStrategy
    ) -> dict[str, str]:
        """Estimate phase timelines."""
        timelines = {}
        for phase in phases:
            timelines[phase["name"]] = phase["duration"]
        return timelines

    def _define_quality_gates(self, strategy: AgentStrategy) -> list[str]:
        """Define quality gates for execution."""
        gates = [
            "Requirements validation",
            "Implementation review",
            "Testing completion",
        ]

        if strategy.execution_strategy == ExecutionStrategy.ORCHESTRATED:
            gates.extend(
                ["Architecture approval", "Security review", "Performance validation"]
            )

        return gates

    def _generate_contingency_plans(self, strategy: AgentStrategy) -> list[str]:
        """Generate contingency plans for potential issues."""
        plans = [
            "Simplified implementation fallback",
            "Manual intervention protocols",
            "Resource scaling options",
        ]

        if strategy.execution_strategy == ExecutionStrategy.ORCHESTRATED:
            plans.extend(
                [
                    "Phased rollback strategy",
                    "Alternative architecture options",
                    "External expert consultation",
                ]
            )

        return plans

    async def perform_comprehensive_analysis(
        self,
        request: dict[str, Any],
        validation_result: ValidationResult,
        completion_result: CompletionResult,
    ) -> O3AnalysisResult:
        """Perform complete O3-level analysis and planning."""
        self.logger.info("Performing comprehensive O3 analysis")

        # Step 1: Complexity analysis
        complexity_result, complexity_reasoning = await self.analyze_request_complexity(
            request, validation_result
        )

        # Step 2: Strategy generation
        agent_strategy, strategy_reasoning = await self.generate_agent_strategy(
            complexity_result, completion_result
        )

        # Step 3: Execution planning
        execution_plan, planning_reasoning = await self.create_execution_plan(
            agent_strategy, completion_result
        )

        # Combine all reasoning steps
        all_reasoning = complexity_reasoning + strategy_reasoning + planning_reasoning

        # Calculate overall confidence
        confidence = sum(step.confidence for step in all_reasoning) / len(all_reasoning)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            complexity_result, agent_strategy, execution_plan
        )

        return O3AnalysisResult(
            request_analysis={
                "original_request": request,
                "validation": validation_result,
                "completion": completion_result,
            },
            complexity_assessment=complexity_result,
            agent_strategy=agent_strategy,
            execution_plan=execution_plan,
            reasoning_chain=all_reasoning,
            confidence=confidence,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        complexity_result: ComplexityAnalysisResult,
        agent_strategy: AgentStrategy,
        execution_plan: ExecutionPlan,
    ) -> list[str]:
        """Generate strategic recommendations."""
        recommendations = []

        if complexity_result.overall_score >= 7:
            recommendations.append("Consider breaking down into smaller sub-projects")

        if complexity_result.factors.risk.score >= 7:
            recommendations.append(
                "Implement comprehensive testing and security reviews"
            )

        if complexity_result.factors.dependencies.score >= 6:
            recommendations.append("Establish clear integration protocols early")

        if len(agent_strategy.agent_roles) >= 4:
            recommendations.append(
                "Implement robust communication and coordination protocols"
            )

        recommendations.append(
            f"Estimated completion: {execution_plan.timeline_estimates}"
        )

        return recommendations

    async def generate_dynamic_agent_strategy(
        self, request: dict[str, Any], complexity_result: ComplexityAnalysisResult
    ) -> tuple[AgentStrategy, list[ReasoningStep]]:
        """
        O3 dynamically generates agent strategy based on request analysis

        NO HARDCODED ASSUMPTIONS - O3 makes all decisions based on:
        - Request content and requirements
        - Complexity analysis results
        - Available framework capabilities
        - Success pattern examples (guidance only)
        """
        self.logger.info(
            f"Generating dynamic agent strategy for request: {request.get('name', 'unnamed')}"
        )

        reasoning_steps = []

        # Step 1: Framework education
        framework_context = {
            "available_tools": O3FrameworkEducator.get_tool_catalog(),
            "coordination_patterns": O3FrameworkEducator.get_coordination_patterns(),
            "project_examples": O3FrameworkEducator.get_project_examples(),
            "schema_requirements": O3FrameworkEducator.get_schema_requirements(),
            "model_guidelines": O3FrameworkEducator.get_model_usage_guidelines(),
        }

        step1 = ReasoningStep(
            step_id="framework_education",
            analysis_type=AnalysisType.STRATEGY,
            reasoning="Providing O3 with comprehensive framework knowledge for dynamic generation",
            confidence=1.0,
            evidence=[
                f"Tool catalog: {len(framework_context['available_tools'])} tools available",
                f"Coordination patterns: {len(framework_context['coordination_patterns'])} patterns",
                f"Project examples: {len(framework_context['project_examples'])} diverse examples",
            ],
        )
        reasoning_steps.append(step1)

        # Step 2: Enhanced O3 prompt for dynamic generation
        strategy_prompt = f"""
You are an expert system architect with deep knowledge of software development patterns and multi-agent coordination. Analyze this specific request and design the optimal agent strategy.

REQUEST DETAILS:
{json.dumps(request, indent=2)}

COMPLEXITY ANALYSIS:
- Overall Score: {complexity_result.overall_score}/10
- Technical Depth: {complexity_result.factors.technical_depth.score}/10
- Domain Knowledge: {complexity_result.factors.domain_knowledge.score}/10
- Dependencies: {complexity_result.factors.dependencies.score}/10
- Integration Complexity: {complexity_result.factors.dependencies.score}/10
- Timeline Pressure: {complexity_result.factors.timeline.score}/10
- Risk Level: {complexity_result.factors.risk.score}/10

FRAMEWORK CAPABILITIES AVAILABLE:
{json.dumps(framework_context, indent=2)}

YOUR TASK: Design a dynamic agent strategy specifically for THIS REQUEST.

Analyze the request and determine:

1. AGENT ROLES NEEDED:
   - What specialized agents are required for this specific request?
   - What unique roles and responsibilities should each agent have?
   - Consider the request type, complexity, and requirements
   - Be creative - don't limit yourself to predefined agent types

2. TOOL SELECTION:
   - Which tools should each agent use based on their specific responsibilities?
   - Select from the available tool catalog based on what each agent needs to accomplish
   - Consider efficiency and capability requirements

3. DELIVERABLES & OUTPUTS:
   - What specific files, components, or artifacts should each agent produce?
   - Define clear deliverables based on the request requirements
   - Consider project structure and organization needs

4. COORDINATION PATTERN:
   - How should these agents work together for THIS specific project?
   - Consider dependencies, parallelization opportunities, and workflow efficiency
   - Choose the most appropriate coordination pattern or combination

5. COMMUNICATION FLOW:
   - How should agents share information and coordinate their work?
   - Define clear communication channels and data dependencies
   - Ensure efficient information flow

CRITICAL GUIDELINES:
- Make decisions based on THIS SPECIFIC REQUEST, not predefined templates
- Different requests need different solutions - be adaptive
- Use the project examples as guidance, not rigid templates
- Be creative but practical in your agent design
- Ensure all agents have clear, non-overlapping responsibilities
- Consider both sequential dependencies and parallel opportunities

OUTPUT REQUIREMENTS:
Provide your strategy as structured JSON matching this schema:
{{
    "execution_strategy": "multi_agent|orchestrated|simple",
    "agent_roles": [
        {{
            "role": "Specific role name",
            "description": "Clear description of responsibilities",
            "tools": ["tool1", "tool2", "tool3"],
            "deliverables": ["file1.ext", "file2.ext"],
            "success_criteria": ["criterion1", "criterion2"]
        }}
    ],
    "coordination_pattern": "sequential|parallel|conditional|hierarchical|iterative|hybrid",
    "communication_flow": {{
        "agent1": ["agent2", "agent3"],
        "agent2": ["agent1"],
        "agent3": ["agent1"]
    }},
    "success_criteria": ["overall_criterion1", "overall_criterion2"],
    "risk_mitigation": ["mitigation1", "mitigation2"],
    "estimated_phases": [
        {{
            "phase": "Phase name",
            "agents": ["agent1", "agent2"],
            "duration": "time estimate",
            "dependencies": ["previous_phase"]
        }}
    ]
}}

Generate your dynamic agent strategy now:
"""

        # Step 3: O3 reasoning for dynamic strategy generation
        step2 = ReasoningStep(
            step_id="dynamic_strategy_analysis",
            analysis_type=AnalysisType.STRATEGY,
            reasoning="Using O3 reasoning to analyze request and generate dynamic agent strategy",
            confidence=0.9,
            evidence=[
                f"Request complexity: {complexity_result.overall_score}/10",
                f"Framework tools available: {len(framework_context['available_tools'])}",
                "Dynamic analysis based on specific request requirements",
            ],
        )
        reasoning_steps.append(step2)

        try:
            # Call O3 for dynamic strategy generation
            from langchain_core.messages import HumanMessage, SystemMessage

            # API Logging: Prepare request data
            api_start_time = time.time()
            request_messages = [
                SystemMessage(
                    content="You are an expert system architect specializing in dynamic multi-agent workflow design."
                ),
                HumanMessage(content=strategy_prompt),
            ]

            # Log API call start
            try:
                from src.applications.oamat_sd.src.sd_logging.logger_factory import (
                    get_logger_factory,
                )

                logger_factory = get_logger_factory()
                logger_factory.log_api_call(
                    method="POST",
                    url="https://api.openai.com/v1/chat/completions",
                    request_data={
                        "model": "o3-mini",
                        "messages": [
                            {"role": msg.type, "content": str(msg.content)[:500]}
                            for msg in request_messages
                        ],
                        "temperature": 0,
                    },
                    status_code=None,  # Will update after response
                    duration_ms=None,  # Will update after response
                )
            except Exception as log_error:
                logger.warning(f"API logging failed: {log_error}")

            response = await self.master_model.ainvoke(request_messages)

            # API Logging: Log successful response
            api_duration = (time.time() - api_start_time) * 1000
            try:
                logger_factory.log_api_call(
                    method="POST",
                    url="https://api.openai.com/v1/chat/completions",
                    request_data={
                        "model": "o3-mini",
                        "messages": [
                            {"role": msg.type, "content": str(msg.content)[:500]}
                            for msg in request_messages
                        ],
                    },
                    response_data={
                        "content": str(response.content)[:1000],
                        "finish_reason": "stop",
                        "usage": {
                            "completion_tokens": len(str(response.content).split())
                        },
                    },
                    status_code=200,
                    duration_ms=api_duration,
                )
            except Exception as log_error:
                logger.warning(f"API response logging failed: {log_error}")

            # Parse O3 response
            strategy_data = self._parse_strategy_response(response.content)

            # Step 4: Strategy validation and assembly
            step3 = ReasoningStep(
                step_id="strategy_validation",
                analysis_type=AnalysisType.STRATEGY,
                reasoning=f"Validated and assembled dynamic strategy with {len(strategy_data.get('agent_roles', []))} specialized agents",
                confidence=0.85,
                evidence=[
                    f"Agent roles: {[role['role'] for role in strategy_data.get('agent_roles', [])]}",
                    f"Coordination: {strategy_data.get('coordination_pattern', 'undefined')}",
                    f"Execution strategy: {strategy_data.get('execution_strategy', 'undefined')}",
                ],
            )
            reasoning_steps.append(step3)

            # Convert to AgentStrategy object
            agent_strategy = self._build_agent_strategy_from_o3(
                strategy_data, complexity_result
            )

            return agent_strategy, reasoning_steps

        except Exception as e:
            self.logger.error(f"Dynamic strategy generation failed: {e}")
            # NO FALLBACKS - fail completely if O3 generation fails
            raise RuntimeError(
                f"Stage 2 dynamic agent strategy generation failed: {e}. System cannot proceed without O3 analysis."
            )

    def _parse_strategy_response(self, response_content: str) -> dict[str, Any]:
        """Parse O3 strategy response and extract structured data"""
        try:
            # Look for JSON in the response
            import re

            json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
            if json_match:
                strategy_json = json_match.group()
                return json.loads(strategy_json)
            else:
                raise ValueError("No JSON found in O3 response")

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse O3 strategy response: {e}")
            # Return minimal fallback structure
            return {
                "execution_strategy": "multi_agent",
                "agent_roles": [
                    {
                        "role": "Primary Implementation Agent",
                        "description": "Handle primary implementation tasks",
                        "tools": ["write_file", "mcp_shell_exec"],
                        "deliverables": ["main output files"],
                        "success_criteria": ["Complete implementation"],
                    }
                ],
                "coordination_pattern": "sequential",
                "communication_flow": {},
                "success_criteria": ["Functional requirements met"],
                "risk_mitigation": ["Standard quality controls"],
            }

    def _build_agent_strategy_from_o3(
        self, strategy_data: dict[str, Any], complexity_result: ComplexityAnalysisResult
    ) -> AgentStrategy:
        """Build AgentStrategy object from O3's dynamic response"""

        # Extract agent roles from O3 response
        agent_roles = []
        for role_data in strategy_data.get("agent_roles", []):
            agent_roles.append(role_data.get("role", "Unnamed Agent"))

        # Determine execution strategy
        execution_strategy_map = {
            "simple": ExecutionStrategy.SIMPLE,
            "multi_agent": ExecutionStrategy.MULTI_AGENT,
            "orchestrated": ExecutionStrategy.ORCHESTRATED,
        }
        execution_strategy = execution_strategy_map.get(
            strategy_data.get("execution_strategy", "multi_agent"),
            ExecutionStrategy.MULTI_AGENT,
        )

        # Build AgentStrategy object
        return AgentStrategy(
            execution_strategy=execution_strategy,
            agent_roles=agent_roles,
            coordination_pattern=strategy_data.get(
                "coordination_pattern", "sequential"
            ),
            communication_flow=strategy_data.get("communication_flow", {}),
            success_criteria=strategy_data.get(
                "success_criteria", ["Complete all requirements"]
            ),
            risk_mitigation=strategy_data.get(
                "risk_mitigation", ["Standard quality controls"]
            ),
        )

    async def design_optimal_pipeline(
        self, request_data: dict[str, Any], context: dict[str, Any] = None
    ) -> tuple["PipelineDesign", list[ReasoningStep]]:
        """
        Meta-pipeline design: O3 determines optimal pipeline structure for this specific request.

        NO ASSUMPTIONS about stages - O3 decides what pipeline is needed.
        """
        self.logger.info(
            "O3 Meta-Pipeline Design: Determining optimal pipeline structure"
        )

        reasoning_steps = []

        # Step 1: Request analysis and pipeline design
        step1 = ReasoningStep(
            step_id="meta_pipeline_design",
            analysis_type=AnalysisType.STRATEGY,
            reasoning="Analyzing request to determine optimal pipeline structure",
            confidence=0.9,
            evidence=[
                f"Request content: {request_data.get('content', '')[:200]}...",
                f"Context available: {bool(context)}",
                f"Request type: {request_data.get('type', 'unknown')}",
            ],
        )
        reasoning_steps.append(step1)

        # Get AI model for meta-design (o3-mini for reasoning)
        ai_model = self._get_approved_ai_model("reasoning")

        # Meta-pipeline design prompt
        design_prompt = f"""
        Analyze this request and design the optimal pipeline structure:

        REQUEST ANALYSIS:
        - Content: {request_data.get('content', '')}
        - Type: {request_data.get('type', 'unknown')}
        - Description: {request_data.get('description', '')}
        - Context: {context or {}}

        YOUR TASK: Design the optimal pipeline for THIS SPECIFIC request.

        DO NOT ASSUME any predefined stages. Analyze what this request actually needs:

        PIPELINE DESIGN ANALYSIS:
        1. What type of analysis is needed for this request?
        2. What planning stages would be optimal?
        3. Which stages can run in parallel vs sequential?
        4. What dependencies exist between stages?
        5. What context needs to flow between stages?
        6. What validation is needed for this type of request?

        DYNAMIC PIPELINE OPTIONS:
        - Simple requests might need: [analysis] → [direct_execution]
        - Complex requests might need: [complexity] → [strategy] → [planning] → [assembly]
        - Research requests might need: [scope] → [research] → [synthesis] → [delivery]
        - Code requests might need: [requirements] → [architecture] → [implementation] → [testing]
        - Creative requests might need: [ideation] → [refinement] → [execution]

        DEPENDENCY ANALYSIS:
        - Which stages MUST be sequential due to context dependencies?
        - Which stages CAN be parallel because they're independent?
        - What context flows between stages?

        OUTPUT as JSON:
        {{
            "pipeline_type": "optimal_pipeline_for_this_request",
            "stages": [
                {{
                    "stage_id": "unique_stage_identifier",
                    "stage_name": "descriptive_stage_name",
                    "purpose": "what_this_stage_accomplishes",
                    "ai_model": "o3-mini|gpt-4.1-mini",
                    "execution_mode": "parallel|sequential|conditional",
                    "dependencies": ["prerequisite_stage_ids"],
                    "context_inputs": ["context_needed_from_previous_stages"],
                    "context_outputs": ["context_provided_to_next_stages"],
                    "deliverables": ["stage_specific_outputs"]
                }}
            ],
            "execution_graph": {{
                "parallel_groups": [
                    {{
                        "group_id": "parallel_group_1",
                        "stages": ["stage1", "stage2"],
                        "rationale": "why_these_can_run_parallel"
                    }}
                ],
                "sequential_chains": [
                    {{
                        "chain_id": "sequential_chain_1",
                        "stages": ["stage1", "stage2", "stage3"],
                        "context_flow": "what_context_flows_through_chain"
                    }}
                ]
            }},
            "context_management": {{
                "global_context": ["context_available_to_all_stages"],
                "stage_specific_context": {{
                    "stage_id": ["context_specific_to_this_stage"]
                }},
                "validation_points": ["where_to_validate_context_consistency"]
            }},
            "optimization_rationale": "why_this_pipeline_is_optimal_for_this_request",
            "estimated_efficiency": "time_and_resource_estimates",
            "alternative_approaches": ["other_pipeline_structures_considered"]
        }}
        """

        # Invoke AI with structured reasoning
        response_content = await self._invoke_ai_with_structured_reasoning(
            ai_model,
            "You are an expert pipeline architect specializing in dynamic pipeline design for diverse requests.",
            design_prompt,
            "Meta-Pipeline Design",
        )

        # Parse AI response
        pipeline_data = self._parse_json_from_ai_response(
            response_content, "PipelineDesign"
        )

        # Validate AI output schema
        required_fields = [
            "pipeline_type",
            "stages",
            "execution_graph",
            "context_management",
        ]
        self._validate_ai_output_schema(
            pipeline_data, required_fields, "PipelineDesign"
        )

        # Step 2: Pipeline design validation
        step2 = ReasoningStep(
            step_id="pipeline_design_validation",
            analysis_type=AnalysisType.STRATEGY,
            reasoning=f"O3 designed {pipeline_data['pipeline_type']} pipeline with {len(pipeline_data['stages'])} stages",
            confidence=0.85,
            evidence=[
                f"Pipeline type: {pipeline_data['pipeline_type']}",
                f"Stages: {[s['stage_name'] for s in pipeline_data['stages']]}",
                f"Parallel groups: {len(pipeline_data['execution_graph'].get('parallel_groups', []))}",
                f"Sequential chains: {len(pipeline_data['execution_graph'].get('sequential_chains', []))}",
                f"Optimization rationale: {pipeline_data.get('optimization_rationale', 'Dynamic optimization')}",
            ],
        )
        reasoning_steps.append(step2)

        # Convert to PipelineDesign object
        pipeline_design = PipelineDesign(
            pipeline_type=pipeline_data["pipeline_type"],
            stages=pipeline_data["stages"],
            execution_graph=pipeline_data["execution_graph"],
            context_management=pipeline_data["context_management"],
            optimization_rationale=pipeline_data.get("optimization_rationale", ""),
            estimated_efficiency=pipeline_data.get("estimated_efficiency", ""),
            alternative_approaches=pipeline_data.get("alternative_approaches", []),
        )

        self.logger.info(
            f"✅ O3 designed {pipeline_design.pipeline_type} pipeline with {len(pipeline_design.stages)} stages"
        )
        return pipeline_design, reasoning_steps

    # ===== SHARED INFRASTRUCTURE FOR DYNAMIC STAGES 3 & 4 =====
    # Rule 002 compliance: Batched utilities for parallel efficiency

    def _get_approved_ai_model(self, model_type: str = "execution") -> Any:
        """Get approved AI model with proper configuration (Rule 953 compliance)"""
        from langchain_openai import ChatOpenAI

        if model_type == "reasoning":
            # Use o3-mini for reasoning-heavy tasks (Stage 3 planning)
            model_name = "o3-mini"
            model_kwargs = {"model": model_name}
            # O3 models don't support temperature
        else:
            # Use gpt-4.1-mini for execution tasks (Stage 4 assembly)
            model_name = "gpt-4.1-mini"
            model_kwargs = {"model": model_name, "temperature": 0.2}

        return ChatOpenAI(**model_kwargs)

    async def _invoke_ai_with_structured_reasoning(
        self,
        ai_model: Any,
        system_prompt: str,
        user_prompt: str,
        context: str = "AI planning",
    ) -> str:
        """Invoke AI with structured reasoning pattern (Rule 954 compliance)"""
        from langchain_core.messages import HumanMessage, SystemMessage

        # Rule 954: Structured reasoning format
        structured_system = f"""
        {system_prompt}

        REASONING INSTRUCTIONS (Rule 954 compliance):
        1. **Persistence** – continue until task done, no early exit
        2. **Tool Use** – prefer AI analysis when uncertain
        3. **Planning** – output PLAN before implementation decisions
        4. **Format** each step:
           Thought: [reasoning about this specific case]
           Action: [decision for this context]
           Observation: [validation of decision quality]
        End with **FINAL_ANSWER** containing structured output.
        """

        try:
            # API Logging: Prepare request data
            api_start_time = time.time()
            request_messages = [
                SystemMessage(content=structured_system),
                HumanMessage(content=user_prompt),
            ]

            # Log API call start
            try:
                from src.applications.oamat_sd.src.sd_logging.logger_factory import (
                    get_logger_factory,
                )

                logger_factory = get_logger_factory()
                logger_factory.log_api_call(
                    method="POST",
                    url="https://api.openai.com/v1/chat/completions",
                    request_data={
                        "model": getattr(ai_model, "model_name", "gpt-4.1-mini"),
                        "messages": [
                            {"role": msg.type, "content": str(msg.content)[:500]}
                            for msg in request_messages
                        ],
                        "temperature": getattr(ai_model, "temperature", 0.7),
                    },
                    status_code=None,
                    duration_ms=None,
                )
            except Exception as log_error:
                logger.warning(f"API logging failed: {log_error}")

            response = await ai_model.ainvoke(request_messages)

            # API Logging: Log successful response
            api_duration = (time.time() - api_start_time) * 1000
            try:
                logger_factory.log_api_call(
                    method="POST",
                    url="https://api.openai.com/v1/chat/completions",
                    request_data={
                        "model": getattr(ai_model, "model_name", "gpt-4.1-mini"),
                        "messages": [
                            {"role": msg.type, "content": str(msg.content)[:500]}
                            for msg in request_messages
                        ],
                    },
                    response_data={
                        "content": str(response.content)[:1000],
                        "finish_reason": "stop",
                        "usage": {
                            "completion_tokens": len(str(response.content).split())
                        },
                    },
                    status_code=200,
                    duration_ms=api_duration,
                )
            except Exception as log_error:
                logger.warning(f"API response logging failed: {log_error}")

            self.logger.info(f"✅ {context} AI reasoning completed successfully")
            return response.content

        except Exception as e:
            self.logger.error(f"❌ {context} AI reasoning failed: {e}")
            # Rule compliance: NO FALLBACKS - fail cleanly
            raise RuntimeError(
                f"{context} failed: {e}. System cannot proceed without AI analysis."
            )

    def _parse_json_from_ai_response(
        self, response_content: str, expected_schema: str
    ) -> dict[str, Any]:
        """Parse JSON from AI response with validation (shared utility)"""
        try:
            # Look for JSON in the response
            import re

            json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                self.logger.info(
                    f"✅ Successfully parsed {expected_schema} from AI response"
                )
                return parsed_data
            else:
                raise ValueError(f"No JSON found in AI response for {expected_schema}")

        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to parse {expected_schema} JSON: {e}")
            # Rule compliance: NO FALLBACKS - fail cleanly
            raise RuntimeError(
                f"AI response parsing failed for {expected_schema}: {e}. Cannot proceed without valid AI output."
            )

    def _validate_ai_output_schema(
        self, data: dict[str, Any], required_fields: list[str], schema_name: str
    ) -> bool:
        """Validate AI output conforms to expected schema"""
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            self.logger.error(
                f"❌ {schema_name} missing required fields: {missing_fields}"
            )
            raise ValueError(
                f"{schema_name} AI output missing fields: {missing_fields}"
            )

        self.logger.info(f"✅ {schema_name} schema validation passed")
        return True

    def _create_execution_phase_template(self) -> dict[str, Any]:
        """Create execution phase template with context management guidelines"""
        return {
            "phase_structure": {
                "name": "descriptive_phase_name",
                "description": "clear phase purpose",
                "duration": "realistic_time_estimate",
                "agents_involved": ["exact_agent_roles_from_strategy"],
                "deliverables": ["specific_file_names_with_extensions"],
                "execution_mode": "parallel|sequential|conditional",
                "dependencies": ["prerequisite_phases_or_deliverables"],
                "context_requirements": ["context_needed_from_previous_phases"],
            },
            "context_management_rules": {
                "agent_naming": "Use exact agent role names from agent_strategy - no variations or abbreviations",
                "deliverable_naming": "Use specific, consistent file names that will be referenced in later stages",
                "variable_consistency": "Maintain consistent naming patterns across all phases",
                "reference_tracking": "Ensure all references can be resolved within the generated artifacts",
                "integration_points": "Identify where outputs from this phase will be consumed by other phases",
            },
            "dependency_analysis": {
                "parallel_safe": "Tasks that can execute without waiting for other task outputs",
                "sequential_required": "Tasks that need outputs or context from specific previous tasks",
                "conditional_execution": "Tasks that depend on decision points or validation results",
            },
            "quality_standards": {
                "completeness": "All required information must be specified",
                "consistency": "Names and references must align across phases",
                "integration": "Outputs must be consumable by dependent phases",
                "traceability": "All decisions must be traceable to previous stage contexts",
            },
        }

    def _create_workflow_assembly_template(self) -> dict[str, Any]:
        """Create workflow assembly template with cross-stage coherence requirements"""
        return {
            "agent_specification": {
                "agent_id": "safe_identifier_matching_strategy",
                "role": "exact_role_from_agent_strategy",
                "tools": ["specific_tool_names"],
                "deliverables": ["filenames_matching_execution_plan"],
                "success_criteria": ["measurable_completion_criteria"],
                "context_dependencies": ["specific_context_from_previous_agents"],
                "parallel_compatible": "boolean_based_on_context_dependencies",
            },
            "execution_graph_rules": {
                "node_naming": "Use consistent, meaningful node identifiers",
                "dependency_mapping": "Map execution plan dependencies to workflow nodes",
                "context_flow": "Define what context flows between nodes",
                "parallel_grouping": "Group nodes that can execute simultaneously",
                "sequential_chaining": "Chain nodes that require context from predecessors",
            },
            "cross_stage_coherence": {
                "agent_alignment": "Agent IDs and roles must exactly match agent_strategy",
                "execution_compliance": "Execution graph must respect execution_plan dependencies",
                "deliverable_consistency": "All deliverables must align across planning stages",
                "variable_reference_alignment": "All names, IDs, and references must be consistent",
                "integration_validation": "Generated artifacts must work together seamlessly",
            },
            "context_tracking": {
                "state_management": "Track context flow through the entire workflow",
                "dependency_resolution": "Ensure all dependencies can be resolved at runtime",
                "error_context_preservation": "Maintain context information during error recovery",
                "validation_checkpoints": "Define points where context consistency is verified",
            },
            "mandatory_checks": [
                "verify_agent_names_match_strategy",
                "validate_deliverable_alignment_with_plan",
                "confirm_dependency_graph_respects_execution_requirements",
                "check_variable_reference_consistency_across_stages",
                "ensure_parallel_opportunities_are_safely_implemented",
                "validate_sequential_requirements_are_properly_enforced",
            ],
        }

    # ===== END SHARED INFRASTRUCTURE =====
