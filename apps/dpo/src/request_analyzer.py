#!/usr/bin/env python3
"""
Request Analyzer Component - DPO System
Parses and classifies development requests for workflow generation
"""

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ProjectType(Enum):
    """Enumeration of supported project types"""

    BACKEND_API = "backend_api"
    FRONTEND_APP = "frontend_app"
    FULL_STACK = "full_stack"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    INTEGRATION = "integration"
    DATA_PIPELINE = "data_pipeline"
    MICROSERVICE = "microservice"
    AUTOMATION = "automation"
    UNKNOWN = "unknown"


class ComplexityLevel(Enum):
    """Project complexity assessment levels"""

    SIMPLE = "simple"  # 5-8 agents
    MODERATE = "moderate"  # 9-15 agents
    COMPLEX = "complex"  # 16-20 agents
    ENTERPRISE = "enterprise"  # 21-25 agents


@dataclass
class TechnologyStack:
    """Identified technology stack and frameworks"""

    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RequestAnalysis:
    """Complete analysis result from request processing"""

    original_request: str
    project_type: ProjectType
    complexity: ComplexityLevel
    tech_stack: TechnologyStack
    phases: List[str]
    estimated_agents: int
    focus_areas: List[str]
    requirements: Dict[str, Any]
    constraints: List[str]
    implicit_requirements: List[str]
    ecosystem_context: Dict[str, Any]
    confidence_score: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "original_request": self.original_request,
            "project_type": self.project_type.value,
            "complexity": self.complexity.value,
            "tech_stack": self.tech_stack.to_dict(),
            "phases": self.phases,
            "estimated_agents": self.estimated_agents,
            "focus_areas": self.focus_areas,
            "requirements": self.requirements,
            "constraints": self.constraints,
            "implicit_requirements": self.implicit_requirements,
            "ecosystem_context": self.ecosystem_context,
            "confidence_score": self.confidence_score,
        }


class RequestAnalyzer:
    """Main request analyzer for DPO system"""

    # Keyword patterns for project type detection
    PROJECT_TYPE_PATTERNS = {
        ProjectType.BACKEND_API: [
            r"\bapi\b",
            r"\brest\b",
            r"\bgraphql\b",
            r"\bendpoint\b",
            r"\bbackend\b",
            r"\bserver\b",
            r"\bmicroservice\b",
        ],
        ProjectType.FRONTEND_APP: [
            r"\bfrontend\b",
            r"\bui\b",
            r"\bweb\s*app\b",
            r"\breact\b",
            r"\bvue\b",
            r"\bangular\b",
            r"\bdashboard\b",
            r"\binterface\b",
        ],
        ProjectType.FULL_STACK: [
            r"\bfull[\s-]?stack\b",
            r"\bweb\s*application\b",
            r"\bfrontend\s*and\s*backend\b",
            r"\bcomplete\s*app\b",
        ],
        ProjectType.CLI_TOOL: [
            r"\bcli\b",
            r"\bcommand[\s-]?line\b",
            r"\bterminal\b",
            r"\bconsole\b",
            r"\bscript\b",
        ],
        ProjectType.LIBRARY: [
            r"\blibrary\b",
            r"\bpackage\b",
            r"\bmodule\b",
            r"\bsdk\b",
            r"\bframework\b",
            r"\btoolkit\b",
        ],
        ProjectType.INTEGRATION: [
            r"\bintegrat\w+\b",
            r"\bconnect\w+\b",
            r"\bbridge\b",
            r"\badapter\b",
            r"\bplugin\b",
            r"\bextension\b",
        ],
        ProjectType.DATA_PIPELINE: [
            r"\bdata\s*pipeline\b",
            r"\betl\b",
            r"\bdata\s*process\w+\b",
            r"\banalytics\b",
            r"\bstreaming\b",
            r"\bbatch\s*process\w+\b",
        ],
        ProjectType.MICROSERVICE: [
            r"\bmicroservice\b",
            r"\bservice\b",
            r"\bcontainer\w+\b",
            r"\bdocker\b",
            r"\bkubernetes\b",
        ],
        ProjectType.AUTOMATION: [
            r"\bautomat\w+\b",
            r"\bworkflow\b",
            r"\bscheduler\b",
            r"\borchestrat\w+\b",
            r"\bbot\b",
        ],
    }

    # Technology detection patterns
    TECH_PATTERNS = {
        "languages": {
            "python": [r"\bpython\b", r"\bdjango\b", r"\bflask\b", r"\bfastapi\b"],
            "javascript": [r"\bjavascript\b", r"\bjs\b", r"\bnode\b", r"\bnodejs\b"],
            "typescript": [r"\btypescript\b", r"\bts\b"],
            "go": [r"\bgolang\b", r"\bgo\b(?!\w)"],
            "rust": [r"\brust\b"],
            "java": [r"\bjava\b(?!script)"],
            "csharp": [r"\bc#\b", r"\bcsharp\b", r"\b\.net\b"],
        },
        "frameworks": {
            "fastapi": [r"\bfastapi\b"],
            "django": [r"\bdjango\b"],
            "flask": [r"\bflask\b"],
            "express": [r"\bexpress\b"],
            "react": [r"\breact\b"],
            "vue": [r"\bvue\b"],
            "angular": [r"\bangular\b"],
            "nextjs": [r"\bnext\.?js\b"],
            "svelte": [r"\bsvelte\b"],
        },
        "databases": {
            "postgresql": [r"\bpostgres\b", r"\bpostgresql\b"],
            "mysql": [r"\bmysql\b"],
            "mongodb": [r"\bmongo\b", r"\bmongodb\b"],
            "redis": [r"\bredis\b"],
            "sqlite": [r"\bsqlite\b"],
            "dynamodb": [r"\bdynamodb\b"],
        },
        "tools": {
            "docker": [r"\bdocker\b"],
            "kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
            "jwt": [r"\bjwt\b", r"\bauth\w*\b"],
            "oauth": [r"\boauth\b"],
            "websocket": [r"\bwebsocket\b", r"\brealtime\b", r"\breal-time\b"],
            "queue": [r"\bqueue\b", r"\bcelery\b", r"\brabbitmq\b"],
            "kafka": [r"\bkafka\b"],
        },
    }

    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        "simple": [
            r"\bsimple\b",
            r"\bbasic\b",
            r"\bminimal\b",
            r"\bprototype\b",
            r"\bpoc\b",
            r"\bproof.of.concept\b",
        ],
        "moderate": [r"\bstandard\b", r"\btypical\b", r"\bcommon\b"],
        "complex": [
            r"\bcomplex\b",
            r"\badvanced\b",
            r"\benterprise\b",
            r"\bscalable\b",
            r"\bdistributed\b",
            r"\bmulti-\w+\b",
        ],
        "features": {
            "authentication": [r"\bauth\w*\b", r"\blogin\b", r"\bsignup\b"],
            "database": [r"\bdatabase\b", r"\bdb\b", r"\bdata\s*store\b"],
            "api": [r"\bapi\b", r"\bendpoint\b"],
            "ui": [r"\bui\b", r"\binterface\b", r"\bfrontend\b"],
            "testing": [r"\btest\w*\b", r"\bqa\b"],
            "deployment": [r"\bdeploy\w*\b", r"\bci/cd\b", r"\bdevops\b"],
            "monitoring": [r"\bmonitor\w*\b", r"\blog\w*\b", r"\bmetric\b"],
            "caching": [r"\bcach\w*\b", r"\bredis\b"],
            "security": [r"\bsecur\w*\b", r"\bencrypt\w*\b", r"\bssl\b"],
        },
    }

    def __init__(self, config: Optional[Dict] = None):
        """Initialize analyzer with optional configuration"""
        self.config = config or {}
        self.classification_cache = {}

    def analyze(self, request: str) -> RequestAnalysis:
        """
        Main analysis method - processes request and returns structured analysis

        Args:
            request: Natural language development request

        Returns:
            RequestAnalysis object with complete classification and context
        """
        logger.info(f"Analyzing request: {request[:100]}...")

        # Clean and normalize request
        normalized_request = self._normalize_request(request)

        # Extract key information
        project_type = self._classify_project_type(normalized_request)
        tech_stack = self._extract_technology_stack(normalized_request)
        complexity = self._assess_complexity(normalized_request, tech_stack)
        phases = self._determine_phases(project_type, complexity)
        estimated_agents = self._estimate_agent_count(complexity, phases)
        focus_areas = self._identify_focus_areas(normalized_request, project_type)
        requirements = self._extract_requirements(normalized_request)
        constraints = self._identify_constraints(normalized_request)
        implicit_reqs = self._infer_implicit_requirements(project_type, tech_stack)
        ecosystem_context = self._generate_ecosystem_context(project_type, tech_stack)
        confidence = self._calculate_confidence(project_type, tech_stack, requirements)

        analysis = RequestAnalysis(
            original_request=request,
            project_type=project_type,
            complexity=complexity,
            tech_stack=tech_stack,
            phases=phases,
            estimated_agents=estimated_agents,
            focus_areas=focus_areas,
            requirements=requirements,
            constraints=constraints,
            implicit_requirements=implicit_reqs,
            ecosystem_context=ecosystem_context,
            confidence_score=confidence,
        )

        logger.info(
            f"Analysis complete: {project_type.value}, {complexity.value}, {estimated_agents} agents"
        )
        return analysis

    def _normalize_request(self, request: str) -> str:
        """Normalize and clean the request text"""
        # Convert to lowercase for pattern matching
        normalized = request.lower()
        # Remove excessive whitespace
        normalized = " ".join(normalized.split())
        return normalized

    def _classify_project_type(self, request: str) -> ProjectType:
        """Classify the project type based on request content"""
        scores = {}

        for proj_type, patterns in self.PROJECT_TYPE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, request, re.IGNORECASE):
                    score += 1
            scores[proj_type] = score

        # Find the best match
        if not scores or all(score == 0 for score in scores.values()):
            return ProjectType.UNKNOWN

        best_type = max(scores, key=scores.get)

        # Check for full-stack indicators
        if (
            scores.get(ProjectType.BACKEND_API, 0) > 0
            and scores.get(ProjectType.FRONTEND_APP, 0) > 0
        ):
            return ProjectType.FULL_STACK

        return best_type

    def _extract_technology_stack(self, request: str) -> TechnologyStack:
        """Extract mentioned technologies and frameworks"""
        stack = TechnologyStack()

        for category, tech_dict in self.TECH_PATTERNS.items():
            for tech_name, patterns in tech_dict.items():
                for pattern in patterns:
                    if re.search(pattern, request, re.IGNORECASE):
                        target_list = getattr(stack, category)
                        if tech_name not in target_list:
                            target_list.append(tech_name)
                        break

        # Apply defaults if nothing specified
        if not stack.languages:
            stack.languages = ["python"]  # Default to Python for solo dev

        return stack

    def _assess_complexity(
        self, request: str, tech_stack: TechnologyStack
    ) -> ComplexityLevel:
        """Assess project complexity based on request and tech stack"""
        complexity_score = 0

        # Check explicit complexity indicators
        for level, patterns in [
            ("simple", self.COMPLEXITY_INDICATORS["simple"]),
            ("complex", self.COMPLEXITY_INDICATORS["complex"]),
        ]:
            for pattern in patterns:
                if re.search(pattern, request, re.IGNORECASE):
                    complexity_score += -1 if level == "simple" else 2

        # Count feature requirements
        feature_count = 0
        for feature, patterns in self.COMPLEXITY_INDICATORS["features"].items():
            for pattern in patterns:
                if re.search(pattern, request, re.IGNORECASE):
                    feature_count += 1
                    break

        complexity_score += feature_count

        # Tech stack complexity
        tech_count = (
            len(tech_stack.languages)
            + len(tech_stack.frameworks)
            + len(tech_stack.databases)
            + len(tech_stack.integrations)
        )
        complexity_score += tech_count // 2

        # Determine complexity level
        if complexity_score <= 3:
            return ComplexityLevel.SIMPLE
        elif complexity_score <= 6:
            return ComplexityLevel.MODERATE
        elif complexity_score <= 10:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.ENTERPRISE

    def _determine_phases(
        self, project_type: ProjectType, complexity: ComplexityLevel
    ) -> List[str]:
        """Determine SDLC phases based on project type and complexity"""
        base_phases = [
            "requirements",
            "architecture",
            "implementation",
            "testing",
            "documentation",
        ]

        # Add phases based on complexity
        if complexity == ComplexityLevel.ENTERPRISE:
            base_phases.insert(2, "detailed_design")
            base_phases.append("deployment")
            base_phases.append("monitoring")
            base_phases.append("optimization")
        elif complexity == ComplexityLevel.COMPLEX:
            base_phases.insert(2, "detailed_design")
            base_phases.append("deployment")
            base_phases.append("monitoring")
        elif complexity == ComplexityLevel.MODERATE:
            base_phases.append("deployment")

        # Add project-specific phases
        if project_type == ProjectType.BACKEND_API:
            base_phases.insert(3, "api_design")
        elif project_type == ProjectType.DATA_PIPELINE:
            base_phases.insert(3, "data_modeling")
        elif project_type == ProjectType.MICROSERVICE:
            base_phases.insert(2, "service_design")
            base_phases.append("containerization")

        return base_phases

    def _estimate_agent_count(
        self, complexity: ComplexityLevel, phases: List[str]
    ) -> int:
        """Estimate number of agents needed based on complexity and phases"""
        base_counts = {
            ComplexityLevel.SIMPLE: 5,
            ComplexityLevel.MODERATE: 10,
            ComplexityLevel.COMPLEX: 15,
            ComplexityLevel.ENTERPRISE: 20,
        }

        base_count = base_counts[complexity]

        # Add agents for additional phases
        phase_agents = len(phases) - 5  # 5 is base phase count
        if phase_agents > 0:
            base_count += phase_agents * 2

        # Cap at maximum
        return min(base_count, 25)

    def _identify_focus_areas(
        self, request: str, project_type: ProjectType
    ) -> List[str]:
        """Identify key focus areas for the project"""
        focus_areas = []

        # Common focus patterns
        focus_patterns = {
            "performance": [
                r"\bperform\w*\b",
                r"\bfast\b",
                r"\bspeed\b",
                r"\boptimiz\w*\b",
            ],
            "security": [r"\bsecur\w*\b", r"\bauth\w*\b", r"\bencrypt\w*\b"],
            "scalability": [r"\bscal\w*\b", r"\bgrow\w*\b", r"\bexpand\w*\b"],
            "user_experience": [r"\bux\b", r"\buser.experience\b", r"\busability\b"],
            "api_design": [r"\bapi\b", r"\bendpoint\b", r"\brest\w*\b"],
            "data_integrity": [
                r"\bdata.integr\w*\b",
                r"\bvalidat\w*\b",
                r"\bconsisten\w*\b",
            ],
            "testing": [r"\btest\w*\b", r"\bqa\b", r"\bquality\b"],
            "documentation": [r"\bdoc\w*\b", r"\bguide\b", r"\btutorial\b"],
        }

        for area, patterns in focus_patterns.items():
            for pattern in patterns:
                if re.search(pattern, request, re.IGNORECASE):
                    focus_areas.append(area)
                    break

        # Add default focus areas based on project type
        if project_type == ProjectType.BACKEND_API:
            if "api_design" not in focus_areas:
                focus_areas.append("api_design")
        elif project_type == ProjectType.FRONTEND_APP:
            if "user_experience" not in focus_areas:
                focus_areas.append("user_experience")

        # Solo developer focus
        if "performance" not in focus_areas:
            focus_areas.append("performance")

        return focus_areas[:5]  # Limit to top 5 focus areas

    def _extract_requirements(self, request: str) -> Dict[str, Any]:
        """Extract explicit requirements from the request"""
        requirements = {
            "functional": [],
            "non_functional": [],
            "features": [],
            "constraints": [],
        }

        # Feature extraction patterns
        feature_patterns = [
            (r"(?:must|should|need to|require)\s+(\w+(?:\s+\w+){0,3})", "functional"),
            (r"(?:with|including|feature[s]?:?)\s+(\w+(?:\s+\w+){0,3})", "features"),
            (
                r"(?:support[s]?|enable[s]?|allow[s]?)\s+(\w+(?:\s+\w+){0,3})",
                "functional",
            ),
        ]

        for pattern, category in feature_patterns:
            matches = re.finditer(pattern, request, re.IGNORECASE)
            for match in matches:
                requirement = match.group(1).strip()
                if requirement and requirement not in requirements[category]:
                    requirements[category].append(requirement)

        return requirements

    def _identify_constraints(self, request: str) -> List[str]:
        """Identify project constraints and limitations"""
        constraints = []

        constraint_patterns = [
            (r"(?:without|no|avoid)\s+(\w+(?:\s+\w+){0,2})", "exclusion"),
            (
                r"(?:limit\w*|restrict\w*|constrain\w*)\s+(\w+(?:\s+\w+){0,2})",
                "limitation",
            ),
            (r"(?:must be|should be)\s+(\w+(?:\s+\w+){0,2})", "requirement"),
            (r"(?:single|solo|one)\s+(\w+)", "scope"),
        ]

        for pattern, constraint_type in constraint_patterns:
            matches = re.finditer(pattern, request, re.IGNORECASE)
            for match in matches:
                constraint = f"{constraint_type}: {match.group(1).strip()}"
                if constraint not in constraints:
                    constraints.append(constraint)

        # Add default solo developer constraints
        constraints.append("scope: single developer")
        constraints.append("limitation: no enterprise complexity")

        return constraints

    def _infer_implicit_requirements(
        self, project_type: ProjectType, tech_stack: TechnologyStack
    ) -> List[str]:
        """Infer implicit requirements based on project type and tech stack"""
        implicit_reqs = []

        # Project type implications
        if project_type == ProjectType.BACKEND_API:
            implicit_reqs.extend(
                [
                    "RESTful design principles",
                    "Input validation and sanitization",
                    "Error handling and status codes",
                    "API documentation (OpenAPI/Swagger)",
                ]
            )
        elif project_type == ProjectType.FRONTEND_APP:
            implicit_reqs.extend(
                [
                    "Responsive design",
                    "Cross-browser compatibility",
                    "User state management",
                    "Accessibility standards",
                ]
            )
        elif project_type == ProjectType.CLI_TOOL:
            implicit_reqs.extend(
                [
                    "Command-line argument parsing",
                    "Help documentation",
                    "Error messages and exit codes",
                    "Configuration file support",
                ]
            )

        # Tech stack implications
        if "python" in tech_stack.languages:
            implicit_reqs.append("Type hints and docstrings")
        if "jwt" in tech_stack.tools:
            implicit_reqs.append("Token refresh mechanism")
        if tech_stack.databases:
            implicit_reqs.append("Database migrations and schema management")

        return implicit_reqs

    def _generate_ecosystem_context(
        self, project_type: ProjectType, tech_stack: TechnologyStack
    ) -> Dict[str, Any]:
        """Generate ecosystem-specific context for the project"""
        context = {
            "environment": "master_root ecosystem",
            "optimization_focus": "solo developer efficiency",
            "available_tools": [],
            "integration_opportunities": [],
            "performance_targets": {},
            "reusable_components": [],
        }

        # Available tools based on ecosystem
        context["available_tools"] = [
            "agent-orchestrator",
            "knowledge_system (mcp__knowledge)",
            "monitoring-dashboard",
            "claude-monitor",
        ]

        # Integration opportunities
        if project_type in [ProjectType.BACKEND_API, ProjectType.FULL_STACK]:
            context["integration_opportunities"].append(
                "monitoring-dashboard integration"
            )

        if tech_stack.databases:
            context["integration_opportunities"].append("existing database connections")

        # Performance targets for solo dev
        context["performance_targets"] = {
            "response_time": "< 100ms for API calls",
            "startup_time": "< 2 seconds",
            "memory_usage": "< 500MB",
            "cpu_usage": "minimal background processing",
        }

        # Reusable components from ecosystem
        context["reusable_components"] = [
            "TokenPool from orchestrator",
            "AsyncIO patterns",
            "Logging infrastructure",
            "Configuration management",
        ]

        return context

    def _calculate_confidence(
        self, project_type: ProjectType, tech_stack: TechnologyStack, requirements: Dict
    ) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 0.4  # Base confidence (lowered)

        # Project type confidence
        if project_type != ProjectType.UNKNOWN:
            confidence += 0.25

        # Tech stack specificity
        if tech_stack.languages or tech_stack.frameworks:
            confidence += 0.2

        # Requirements clarity
        if requirements["functional"] or requirements["features"]:
            confidence += 0.15

        # Cap at 1.0
        return min(confidence, 1.0)

    def validate_analysis(self, analysis: RequestAnalysis) -> Tuple[bool, List[str]]:
        """
        Validate the analysis for completeness and consistency

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check project type
        if analysis.project_type == ProjectType.UNKNOWN:
            issues.append("Could not determine project type")

        # Check tech stack
        if not analysis.tech_stack.languages:
            issues.append("No programming language identified")

        # Check agent count
        if analysis.estimated_agents < 5:
            issues.append("Insufficient agents for meaningful workflow")
        elif analysis.estimated_agents > 25:
            issues.append("Agent count exceeds maximum limit")

        # Check phases
        if len(analysis.phases) < 3:
            issues.append("Insufficient SDLC phases defined")

        # Check confidence
        if analysis.confidence_score < 0.5:
            issues.append("Low confidence in analysis")

        is_valid = len(issues) == 0
        return is_valid, issues
