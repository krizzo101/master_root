"""Intelligent mode detection for task execution"""

import re
from enum import Enum, auto
from typing import Optional, Dict, List
from dataclasses import dataclass, field


class ExecutionMode(Enum):
    """Execution modes for Claude Code servers"""

    # Primary modes
    CODE = auto()  # Code generation/modification
    ANALYSIS = auto()  # Code analysis and understanding
    REVIEW = auto()  # Code review and critique
    TESTING = auto()  # Test generation and execution
    DOCUMENTATION = auto()  # Documentation generation
    REFACTOR = auto()  # Code refactoring
    DEBUG = auto()  # Debugging and fixing

    # Composite modes
    FULL_CYCLE = auto()  # Code + Test + Doc + Review
    QUALITY = auto()  # Code + Review + Test
    RAPID = auto()  # Code only, minimal checks

    # Special modes
    LEARNING = auto()  # Learn from codebase
    MIGRATION = auto()  # Code migration/upgrade


@dataclass
class ModeConfiguration:
    """Configuration for each execution mode"""

    mode: ExecutionMode
    primary_agents: List[str] = field(default_factory=list)
    support_agents: List[str] = field(default_factory=list)
    validation_required: bool = True
    documentation_required: bool = False
    testing_required: bool = True
    review_iterations: int = 1
    quality_threshold: float = 0.8
    timeout_multiplier: float = 1.0

    # Agent settings
    enable_critic: bool = True
    enable_tester: bool = True
    enable_documenter: bool = False
    enable_security: bool = False

    # Workflow settings
    parallel_agents: bool = True
    iterative_refinement: bool = False
    auto_fix_issues: bool = True

    # Resource settings
    max_agent_memory_mb: int = 512
    max_agent_timeout_ms: int = 120000


class ModeDetector:
    """Intelligently detect the appropriate execution mode"""

    def __init__(self, config=None):
        self.config = config
        self.patterns = self._compile_patterns()
        self.mode_configs = self._initialize_mode_configs()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for intent detection"""
        return {
            "generate": re.compile(
                r"\b(create|implement|build|develop|write|generate|make|add)\b",
                re.IGNORECASE,
            ),
            "analyze": re.compile(
                r"\b(analyze|understand|examine|investigate|explore|study|review)\b",
                re.IGNORECASE,
            ),
            "review": re.compile(
                r"\b(review|critique|evaluate|assess|audit|inspect)\b", re.IGNORECASE
            ),
            "test": re.compile(
                r"\b(test|validate|verify|check|ensure|confirm)\b", re.IGNORECASE
            ),
            "document": re.compile(
                r"\b(document|describe|explain|annotate|comment|readme)\b",
                re.IGNORECASE,
            ),
            "fix": re.compile(
                r"\b(fix|debug|resolve|repair|solve|troubleshoot)\b", re.IGNORECASE
            ),
            "improve": re.compile(
                r"\b(refactor|optimize|improve|enhance|clean|reorganize)\b",
                re.IGNORECASE,
            ),
        }

    def _initialize_mode_configs(self) -> Dict[ExecutionMode, ModeConfiguration]:
        """Initialize configurations for each mode"""
        return {
            ExecutionMode.CODE: ModeConfiguration(
                mode=ExecutionMode.CODE,
                primary_agents=["code_generator"],
                support_agents=["critic", "tester"],
                validation_required=True,
                testing_required=True,
                review_iterations=1,
            ),
            ExecutionMode.ANALYSIS: ModeConfiguration(
                mode=ExecutionMode.ANALYSIS,
                primary_agents=["analyzer"],
                support_agents=["documenter"],
                validation_required=False,
                testing_required=False,
                documentation_required=True,
                enable_critic=False,
                enable_tester=False,
                enable_documenter=True,
            ),
            ExecutionMode.REVIEW: ModeConfiguration(
                mode=ExecutionMode.REVIEW,
                primary_agents=["critic"],
                support_agents=["security", "performance"],
                validation_required=True,
                testing_required=False,
                review_iterations=2,
                enable_critic=True,
                enable_security=True,
            ),
            ExecutionMode.TESTING: ModeConfiguration(
                mode=ExecutionMode.TESTING,
                primary_agents=["tester"],
                support_agents=["critic"],
                validation_required=True,
                testing_required=True,
                enable_tester=True,
                enable_critic=True,
            ),
            ExecutionMode.DOCUMENTATION: ModeConfiguration(
                mode=ExecutionMode.DOCUMENTATION,
                primary_agents=["documenter"],
                support_agents=[],
                validation_required=False,
                testing_required=False,
                documentation_required=True,
                enable_documenter=True,
                enable_critic=False,
                enable_tester=False,
            ),
            ExecutionMode.REFACTOR: ModeConfiguration(
                mode=ExecutionMode.REFACTOR,
                primary_agents=["refactorer"],
                support_agents=["critic", "tester"],
                validation_required=True,
                testing_required=True,
                review_iterations=2,
                iterative_refinement=True,
            ),
            ExecutionMode.DEBUG: ModeConfiguration(
                mode=ExecutionMode.DEBUG,
                primary_agents=["debugger"],
                support_agents=["tester", "critic"],
                validation_required=True,
                testing_required=True,
                auto_fix_issues=True,
            ),
            ExecutionMode.FULL_CYCLE: ModeConfiguration(
                mode=ExecutionMode.FULL_CYCLE,
                primary_agents=["code_generator"],
                support_agents=["critic", "tester", "documenter", "security"],
                validation_required=True,
                testing_required=True,
                documentation_required=True,
                review_iterations=2,
                quality_threshold=0.9,
                timeout_multiplier=2.0,
                enable_critic=True,
                enable_tester=True,
                enable_documenter=True,
                enable_security=True,
                iterative_refinement=True,
            ),
            ExecutionMode.QUALITY: ModeConfiguration(
                mode=ExecutionMode.QUALITY,
                primary_agents=["code_generator", "critic"],
                support_agents=["tester", "security"],
                validation_required=True,
                testing_required=True,
                review_iterations=3,
                quality_threshold=0.95,
                iterative_refinement=True,
                enable_critic=True,
                enable_tester=True,
                enable_security=True,
            ),
            ExecutionMode.RAPID: ModeConfiguration(
                mode=ExecutionMode.RAPID,
                primary_agents=["code_generator"],
                support_agents=[],
                validation_required=False,
                testing_required=False,
                documentation_required=False,
                review_iterations=0,
                timeout_multiplier=0.5,
                enable_critic=False,
                enable_tester=False,
                enable_documenter=False,
                parallel_agents=False,
            ),
        }

    def detect_mode(
        self,
        task: str,
        explicit_mode: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> ExecutionMode:
        """Detect the most appropriate mode for the task"""

        # 1. Check for explicit mode override
        if explicit_mode:
            try:
                return ExecutionMode[explicit_mode.upper()]
            except KeyError:
                pass  # Fall through to auto-detection

        # 2. Check context hints
        if context:
            if context.get("mode"):
                try:
                    return ExecutionMode[context["mode"].upper()]
                except KeyError:
                    pass

            # Quality level mapping
            quality_level = context.get("quality_level", "normal")
            if quality_level == "maximum":
                return ExecutionMode.FULL_CYCLE
            elif quality_level == "high":
                return ExecutionMode.QUALITY
            elif quality_level == "rapid":
                return ExecutionMode.RAPID

        # 3. Analyze task intent
        intent = self._analyze_intent(task)

        # 4. Check task complexity and requirements
        complexity = self._analyze_complexity(task)
        has_quality_requirements = self._check_quality_indicators(task)
        is_production = self._check_production_indicators(task, context)

        # 5. Apply heuristics based on intent
        intent_mode_mapping = {
            "generate": ExecutionMode.CODE,
            "analyze": ExecutionMode.ANALYSIS,
            "review": ExecutionMode.REVIEW,
            "test": ExecutionMode.TESTING,
            "document": ExecutionMode.DOCUMENTATION,
            "fix": ExecutionMode.DEBUG,
            "improve": ExecutionMode.REFACTOR,
        }

        base_mode = intent_mode_mapping.get(intent, ExecutionMode.CODE)

        # 6. Upgrade mode based on quality requirements
        if is_production or has_quality_requirements:
            if base_mode == ExecutionMode.CODE:
                if complexity == "very_complex":
                    return ExecutionMode.FULL_CYCLE
                else:
                    return ExecutionMode.QUALITY
            # Other modes remain as detected but with higher quality settings

        # 7. Downgrade for simple tasks
        if complexity == "simple" and not has_quality_requirements:
            if base_mode == ExecutionMode.CODE:
                return ExecutionMode.RAPID

        return base_mode

    def _analyze_intent(self, task: str) -> str:
        """Analyze the primary intent of the task"""

        # Count matches for each intent
        intent_scores = {}

        for intent, pattern in self.patterns.items():
            matches = pattern.findall(task)
            intent_scores[intent] = len(matches)

        # Return intent with highest score
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)

        return "generate"  # Default

    def _analyze_complexity(self, task: str) -> str:
        """Estimate task complexity"""

        # Word count as a basic metric
        word_count = len(task.split())

        # Line count (for multi-line tasks)
        line_count = len(task.split("\n"))

        # Check for complexity indicators
        complex_keywords = [
            "implement",
            "create",
            "develop",
            "build",
            "integrate",
            "multiple",
            "comprehensive",
            "complete",
            "full",
        ]
        very_complex_keywords = [
            "server",
            "framework",
            "architecture",
            "system",
            "infrastructure",
            "enterprise",
            "production",
        ]

        task_lower = task.lower()

        complex_count = sum(1 for kw in complex_keywords if kw in task_lower)
        very_complex_count = sum(1 for kw in very_complex_keywords if kw in task_lower)

        # Heuristics for complexity
        if very_complex_count >= 2 or (word_count > 100 and complex_count >= 3):
            return "very_complex"
        elif complex_count >= 2 or word_count > 50 or line_count > 5:
            return "complex"
        elif word_count > 20 or complex_count >= 1:
            return "moderate"
        else:
            return "simple"

    def _check_quality_indicators(self, task: str) -> bool:
        """Check if task has quality requirements"""

        quality_indicators = [
            "production",
            "quality",
            "robust",
            "secure",
            "maintainable",
            "scalable",
            "professional",
            "best practice",
            "enterprise",
            "critical",
            "reliable",
            "performant",
            "optimized",
        ]

        task_lower = task.lower()
        return any(indicator in task_lower for indicator in quality_indicators)

    def _check_production_indicators(self, task: str, context: Optional[Dict]) -> bool:
        """Check if this is for production use"""

        if context:
            if context.get("environment") == "production":
                return True
            if context.get("is_production", False):
                return True

        prod_indicators = [
            "production",
            "prod",
            "live",
            "deploy",
            "release",
            "customer",
            "client",
        ]

        task_lower = task.lower()
        return any(indicator in task_lower for indicator in prod_indicators)

    def get_mode_config(self, mode: ExecutionMode) -> ModeConfiguration:
        """Get configuration for a specific mode"""
        return self.mode_configs.get(mode, self.mode_configs[ExecutionMode.CODE])

    def suggest_mode_upgrade(
        self, current_mode: ExecutionMode, issues_found: int, quality_score: float
    ) -> Optional[ExecutionMode]:
        """Suggest mode upgrade based on execution results"""

        # If many issues found or low quality, suggest upgrade
        if issues_found > 10 or quality_score < 0.6:
            if current_mode == ExecutionMode.RAPID:
                return ExecutionMode.CODE
            elif current_mode == ExecutionMode.CODE:
                return ExecutionMode.QUALITY
            elif current_mode == ExecutionMode.QUALITY:
                return ExecutionMode.FULL_CYCLE

        return None
