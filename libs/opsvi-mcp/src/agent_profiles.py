"""
Agent Profiles for Recursive MCP Workflows

This module defines standardized agent profiles for different use cases,
ensuring consistent behavior, reporting, and error handling across
recursive Claude Code MCP operations.
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
import json
from enum import Enum


class AgentType(Enum):
    """Types of agents available in the system"""

    RESEARCH = "research"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    ORCHESTRATOR = "orchestrator"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REVIEW = "review"


class OutputFormat(Enum):
    """Supported output formats"""

    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    STRUCTURED = "structured"


@dataclass
class ToolAssignment:
    """Tool assignment configuration for agents"""

    allowed_tools: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    forbidden_tools: List[str] = field(default_factory=list)
    tool_timeout: int = 300
    max_tool_calls: Optional[int] = None


@dataclass
class ReportingTemplate:
    """Standardized reporting template for agent outputs"""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": {"id": "", "type": "", "parent_id": "", "depth": 0, "profile": ""},
            "task": {
                "original": "",
                "interpreted": "",
                "complexity": "",
                "decomposed": False,
            },
            "execution": {
                "start_time": "",
                "end_time": "",
                "duration_seconds": 0,
                "status": "",
                "tools_used": [],
                "files_accessed": [],
                "errors": [],
                "warnings": [],
            },
            "results": {
                "summary": "",
                "details": {},
                "artifacts": [],
                "metrics": {},
                "confidence": 0.0,
            },
            "child_agents": [],
            "recommendations": [],
            "next_steps": [],
        }


@dataclass
class AgentProfile:
    """Complete profile for an agent"""

    name: str
    type: AgentType
    description: str

    # Capabilities
    capabilities: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)

    # Configuration
    output_format: OutputFormat = OutputFormat.JSON
    permission_mode: str = "default"
    timeout: int = 300
    max_retries: int = 3
    max_recursion_depth: int = 3

    # Tool assignments
    tools: Optional[ToolAssignment] = None

    # Reporting
    reporting_template: Optional[ReportingTemplate] = None
    require_structured_output: bool = True

    # Execution settings
    async_execution: bool = True
    parallel_subtasks: bool = True
    max_concurrent_children: int = 5

    # Quality settings
    require_validation: bool = False
    confidence_threshold: float = 0.7

    def to_mcp_config(self) -> Dict[str, Any]:
        """Convert profile to MCP tool configuration"""
        config = {
            "outputFormat": self.output_format.value,
            "permissionMode": self.permission_mode,
            "timeout": self.timeout,
        }

        if self.tools:
            config["allowedTools"] = self.tools.allowed_tools

        return config

    def create_task_prompt(self, task: str, context: Optional[Dict] = None) -> str:
        """Create a standardized prompt for this agent type"""

        prompt = f"""You are a specialized {self.type.value} agent with the following profile:

Profile: {self.name}
Description: {self.description}
Capabilities: {', '.join(self.capabilities)}
Specializations: {', '.join(self.specializations)}

Your task: {task}
"""

        if context:
            prompt += f"\n\nContext:\n{json.dumps(context, indent=2)}"

        if self.require_structured_output:
            prompt += f"\n\nYou must return your response in the following format:\n{json.dumps(self.reporting_template.to_dict() if self.reporting_template else {}, indent=2)}"

        if self.tools and self.tools.required_tools:
            prompt += (
                f"\n\nYou must use these tools: {', '.join(self.tools.required_tools)}"
            )

        return prompt


# Pre-defined Agent Profiles

RESEARCH_AGENT = AgentProfile(
    name="research-specialist",
    type=AgentType.RESEARCH,
    description="Specialized in deep code analysis, pattern recognition, and knowledge extraction",
    capabilities=[
        "code_analysis",
        "pattern_recognition",
        "dependency_mapping",
        "architecture_understanding",
        "documentation_extraction",
    ],
    specializations=[
        "multi_file_analysis",
        "cross_reference_detection",
        "api_discovery",
        "complexity_assessment",
    ],
    tools=ToolAssignment(
        allowed_tools=["*"],
        required_tools=["Grep", "Read", "Glob"],
        forbidden_tools=["Write", "Edit", "Bash"],
    ),
    timeout=600,
    reporting_template=ReportingTemplate(),
)

IMPLEMENTATION_AGENT = AgentProfile(
    name="implementation-specialist",
    type=AgentType.IMPLEMENTATION,
    description="Focused on code generation, modification, and feature implementation",
    capabilities=[
        "code_generation",
        "refactoring",
        "bug_fixing",
        "feature_implementation",
        "api_integration",
    ],
    specializations=[
        "clean_code_principles",
        "design_patterns",
        "performance_optimization",
        "error_handling",
    ],
    tools=ToolAssignment(
        allowed_tools=["*"],
        required_tools=["Write", "Edit", "Read"],
        forbidden_tools=[],
    ),
    require_validation=True,
    permission_mode="default",
)

VALIDATION_AGENT = AgentProfile(
    name="validation-specialist",
    type=AgentType.VALIDATION,
    description="Ensures code quality, correctness, and compliance with standards",
    capabilities=[
        "syntax_validation",
        "type_checking",
        "security_scanning",
        "performance_analysis",
        "best_practice_enforcement",
    ],
    specializations=[
        "automated_testing",
        "code_review",
        "vulnerability_detection",
        "compliance_checking",
    ],
    tools=ToolAssignment(
        allowed_tools=["Read", "Grep", "Bash", "Glob"],
        required_tools=["Bash"],
        forbidden_tools=["Write", "Edit"],
    ),
    async_execution=False,  # Validation should be sequential
    confidence_threshold=0.9,
)

ORCHESTRATOR_AGENT = AgentProfile(
    name="orchestrator-master",
    type=AgentType.ORCHESTRATOR,
    description="Manages complex multi-agent workflows and task decomposition",
    capabilities=[
        "task_decomposition",
        "agent_coordination",
        "workflow_management",
        "result_synthesis",
        "resource_allocation",
    ],
    specializations=[
        "parallel_execution",
        "dependency_resolution",
        "conflict_resolution",
        "optimization",
    ],
    tools=ToolAssignment(
        allowed_tools=["*"], required_tools=["Task"], forbidden_tools=[]
    ),
    max_recursion_depth=5,
    max_concurrent_children=10,
    timeout=1200,
)

ANALYSIS_AGENT = AgentProfile(
    name="analysis-specialist",
    type=AgentType.ANALYSIS,
    description="Performs deep analysis and generates insights from code and data",
    capabilities=[
        "statistical_analysis",
        "trend_detection",
        "anomaly_detection",
        "root_cause_analysis",
        "impact_assessment",
    ],
    specializations=[
        "metrics_calculation",
        "visualization",
        "report_generation",
        "predictive_analysis",
    ],
    tools=ToolAssignment(
        allowed_tools=["Read", "Grep", "Glob", "WebFetch"],
        required_tools=["Read"],
        forbidden_tools=["Write", "Edit", "Bash"],
    ),
    output_format=OutputFormat.STRUCTURED,
)

DOCUMENTATION_AGENT = AgentProfile(
    name="documentation-specialist",
    type=AgentType.DOCUMENTATION,
    description="Creates and maintains comprehensive documentation",
    capabilities=[
        "api_documentation",
        "user_guides",
        "technical_specs",
        "readme_generation",
        "changelog_creation",
    ],
    specializations=[
        "markdown_formatting",
        "diagram_generation",
        "example_creation",
        "cross_referencing",
    ],
    tools=ToolAssignment(
        allowed_tools=["Read", "Write", "Edit", "Grep", "Glob"],
        required_tools=["Write"],
        forbidden_tools=["Bash"],
    ),
    output_format=OutputFormat.MARKDOWN,
)

TESTING_AGENT = AgentProfile(
    name="testing-specialist",
    type=AgentType.TESTING,
    description="Designs and executes comprehensive testing strategies",
    capabilities=[
        "unit_testing",
        "integration_testing",
        "e2e_testing",
        "performance_testing",
        "test_generation",
    ],
    specializations=[
        "test_coverage_analysis",
        "edge_case_detection",
        "mock_generation",
        "test_automation",
    ],
    tools=ToolAssignment(
        allowed_tools=["*"], required_tools=["Bash", "Write"], forbidden_tools=[]
    ),
    require_validation=True,
)

REVIEW_AGENT = AgentProfile(
    name="review-specialist",
    type=AgentType.REVIEW,
    description="Performs thorough code reviews and provides actionable feedback",
    capabilities=[
        "code_review",
        "architecture_review",
        "security_review",
        "performance_review",
        "documentation_review",
    ],
    specializations=[
        "best_practice_identification",
        "anti_pattern_detection",
        "improvement_suggestions",
        "risk_assessment",
    ],
    tools=ToolAssignment(
        allowed_tools=["Read", "Grep", "Glob"],
        required_tools=["Read"],
        forbidden_tools=["Write", "Edit", "Bash"],
    ),
    confidence_threshold=0.8,
)


class AgentProfileManager:
    """Manages agent profiles and assignments"""

    def __init__(self):
        self.profiles: Dict[str, AgentProfile] = {
            "research": RESEARCH_AGENT,
            "implementation": IMPLEMENTATION_AGENT,
            "validation": VALIDATION_AGENT,
            "orchestrator": ORCHESTRATOR_AGENT,
            "analysis": ANALYSIS_AGENT,
            "documentation": DOCUMENTATION_AGENT,
            "testing": TESTING_AGENT,
            "review": REVIEW_AGENT,
        }

    def get_profile(self, name: str) -> Optional[AgentProfile]:
        """Get a profile by name"""
        return self.profiles.get(name)

    def select_agent_for_task(self, task: str, complexity: float) -> AgentProfile:
        """Select the best agent profile for a given task"""

        # Keywords for agent selection
        keywords = {
            "research": ["analyze", "understand", "explore", "investigate", "find"],
            "implementation": ["implement", "create", "build", "write", "develop"],
            "validation": ["validate", "check", "verify", "ensure", "test"],
            "documentation": ["document", "describe", "explain", "readme", "guide"],
            "testing": ["test", "coverage", "mock", "assert", "expect"],
            "review": ["review", "feedback", "improve", "suggest", "critique"],
            "analysis": ["metrics", "statistics", "trends", "insights", "patterns"],
        }

        task_lower = task.lower()

        # Find best match based on keywords
        scores = {}
        for agent_type, words in keywords.items():
            score = sum(1 for word in words if word in task_lower)
            scores[agent_type] = score

        # High complexity tasks should use orchestrator
        if complexity > 0.7:
            return self.profiles["orchestrator"]

        # Select based on keyword matching
        best_match = max(scores, key=scores.get)
        if scores[best_match] > 0:
            return self.profiles[best_match]

        # Default to research for unknown tasks
        return self.profiles["research"]

    def create_agent_chain(self, workflow: List[str]) -> List[AgentProfile]:
        """Create a chain of agents for a workflow"""
        chain = []
        for step in workflow:
            if profile := self.get_profile(step):
                chain.append(profile)
        return chain

    def validate_agent_output(self, output: Dict, profile: AgentProfile) -> bool:
        """Validate that agent output matches expected format"""

        if not profile.require_structured_output:
            return True

        required_fields = ["agent", "task", "execution", "results"]

        for field in required_fields:
            if field not in output:
                return False

        # Check confidence threshold if applicable
        if "confidence" in output.get("results", {}):
            if output["results"]["confidence"] < profile.confidence_threshold:
                return False

        return True


# Workflow Templates

STANDARD_WORKFLOWS = {
    "feature_development": [
        "research",
        "implementation",
        "testing",
        "validation",
        "documentation",
    ],
    "bug_fix": ["analysis", "implementation", "testing", "validation"],
    "code_review": ["research", "review", "documentation"],
    "refactoring": ["analysis", "implementation", "testing", "review"],
    "exploration": ["research", "analysis", "documentation"],
}


def create_recursive_task(
    task: str, profile: AgentProfile, parent_id: Optional[str] = None, depth: int = 0
) -> Dict[str, Any]:
    """Create a properly formatted recursive task for MCP execution"""

    return {
        "task": profile.create_task_prompt(task),
        "config": profile.to_mcp_config(),
        "metadata": {
            "agent_profile": profile.name,
            "agent_type": profile.type.value,
            "parent_id": parent_id,
            "depth": depth,
            "max_depth": profile.max_recursion_depth,
            "timestamp": datetime.now().isoformat(),
        },
    }
