"""
Central Configuration Manager for OAMAT Smart Decomposition

Provides centralized access to all application configuration values.
NO HARDCODED VALUES - All settings must come from configuration files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class ModelConfig:
    """Model configuration settings"""

    model_name: str
    max_tokens: int
    temperature: Optional[float] = None
    supports_temperature: bool = True
    reasoning_effort: Optional[str] = None


@dataclass
class APIConfig:
    """OpenAI API configuration"""

    base_url: str
    timeout_seconds: int
    max_retries: int
    backoff_multiplier: float
    rate_limits: Dict[str, int]


@dataclass
class ExecutionConfig:
    """Execution configuration"""

    agent_timeout_seconds: int
    total_execution_timeout_seconds: int
    max_parallel_agents: int
    max_retry_attempts: int


@dataclass
class ComplexityConfig:
    """Complexity analysis configuration"""

    scoring_thresholds: Dict[str, float]
    execution_mode_threshold: float
    score_mapping: Dict[str, float]  # ADDED - score mapping configuration


@dataclass
class ReasoningConfig:
    """Reasoning configuration for confidence scores"""

    default_confidence_score: float
    high_confidence_score: float
    medium_confidence_score: float
    low_confidence_score: float


@dataclass
class SynthesisConfig:
    """Synthesis configuration for solution scoring"""

    completeness_scoring: Dict[str, float]
    quality_scoring_weights: Dict[str, float]


@dataclass
class InformationCompletionConfig:
    """Information completion configuration"""

    default_confidence: float
    default_data_source: str
    model_temperature: float


@dataclass
class ValidationConfig:
    """Validation configuration"""

    missing_fields_threshold: int
    gap_scoring_divisor: float
    confidence_scores: Dict[str, float]


@dataclass
class ToolsConfig:
    """Tools configuration"""

    defaults: Dict[str, Any]
    recommendations: Dict[str, Any]
    performance: Dict[str, int]
    initialization: Dict[str, int]


@dataclass
class AgentFactoryConfig:
    """Agent factory configuration"""

    memory_defaults: Dict[str, Any]
    performance_defaults: Dict[str, str]
    role_templates: Dict[str, str]
    prompt_defaults: Dict[str, Any]
    counts: Dict[str, int]


@dataclass
class FileProcessingConfig:
    """File processing configuration"""

    language_defaults: Dict[str, str]
    content_processing: Dict[str, Any]


@dataclass
class ContentLimitsConfig:
    """Content processing limits"""

    max_string_length: int
    preview_length: int
    truncation_length: int
    history_max_entries: int
    max_request_length: int


@dataclass
class LoggingConfig:
    """Logging configuration"""

    api_content_limit: int
    console_content_limit: int
    debug_enabled: bool


@dataclass
class QualityConfig:
    """Quality thresholds"""

    minimum_content_length: int
    sophistication_minimum: float
    success_rate_target: float


@dataclass
class EnforcementConfig:
    """Sophistication enforcement settings"""

    runtime_validation: bool
    fail_on_violations: bool
    minimum_compliance: float


@dataclass
class ConstantsConfig:
    """System constants"""

    env_vars: Dict[str, str]
    log_levels: Dict[str, str]
    status: Dict[str, str]
    ui: Dict[str, Dict[str, str]]
    agent_roles: Dict[str, str]
    file_extensions: Dict[str, str]
    config_files: Dict[str, str]
    ui_icons: Dict[str, str]


@dataclass
class DefaultsConfig:
    """Default values for components"""

    frameworks: Dict[str, str]
    api: Dict[str, str]
    scripts: Dict[str, str]
    data_analysis: Dict[str, str]
    automation: Dict[str, str]


@dataclass
class PatternsConfig:
    """Regex patterns and templates"""

    file_parsing: Dict[str, str]
    validation: Dict[str, str]


@dataclass
class MessagesConfig:
    """Message templates"""

    progress: Dict[str, str]


@dataclass
class ErrorMessagesConfig:
    """Error message templates"""

    configuration: Dict[str, str]
    agent: Dict[str, str]
    validation: Dict[str, str]
    strategy: Dict[str, str]
    synthesis: Dict[str, str]


@dataclass
class StatusValuesConfig:
    """Status value constants"""

    health: Dict[str, str]
    execution: Dict[str, str]
    tools: Dict[str, str]
    agents: Dict[str, str]


@dataclass
class AnalysisConfig:
    """Analysis configuration settings"""

    confidence: Dict[str, float]
    complexity: Dict[str, Any]
    ai_integration: Dict[str, Any]
    request_processing: Dict[str, str]
    scoring: Dict[str, Any]


class ConfigManager:
    """Central configuration manager for the application"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self):
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent.parent.parent / "config" / "app_config.yaml"

        if not config_path.exists():
            raise RuntimeError(
                f"Configuration file not found: {config_path} - NO FALLBACKS ALLOWED"
            )

        try:
            with open(config_path) as f:
                raw_config = yaml.safe_load(f)

            if not raw_config:
                # Use a minimal error since config isn't loaded yet
                raise RuntimeError("Configuration file is empty - NO FALLBACKS ALLOWED")

            self._config = self._parse_config(raw_config)

        except Exception as e:
            raise RuntimeError(
                f"Failed to load configuration: {e} - NO FALLBACKS ALLOWED"
            )

    def _parse_config(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw configuration into typed objects"""
        try:
            return {
                "models": {
                    "reasoning": ModelConfig(**raw_config["models"]["reasoning"]),
                    "agent": ModelConfig(**raw_config["models"]["agent"]),
                    "implementation": ModelConfig(
                        **raw_config["models"]["implementation"]
                    ),
                },
                "openai_api": APIConfig(**raw_config["openai_api"]),
                "execution": ExecutionConfig(**raw_config["execution"]),
                "reasoning": ReasoningConfig(**raw_config["reasoning"]),
                "synthesis": SynthesisConfig(**raw_config["synthesis"]),
                "information_completion": InformationCompletionConfig(
                    **raw_config["information_completion"]
                ),
                "validation": ValidationConfig(**raw_config["validation"]),
                "tools": ToolsConfig(**raw_config["tools"]),
                "agent_factory": AgentFactoryConfig(**raw_config["agent_factory"]),
                "file_processing": FileProcessingConfig(
                    **raw_config["file_processing"]
                ),
                "complexity": ComplexityConfig(**raw_config["complexity"]),
                "content_limits": ContentLimitsConfig(**raw_config["content_limits"]),
                "logging": LoggingConfig(**raw_config["logging"]),
                "quality": QualityConfig(**raw_config["quality"]),
                "enforcement": EnforcementConfig(**raw_config["enforcement"]),
                "constants": ConstantsConfig(**raw_config["constants"]),
                "defaults": DefaultsConfig(**raw_config["defaults"]),
                "patterns": PatternsConfig(**raw_config["patterns"]),
                "messages": MessagesConfig(**raw_config["messages"]),
                "error_messages": ErrorMessagesConfig(**raw_config["error_messages"]),
                "status_values": StatusValuesConfig(**raw_config["status_values"]),
                "analysis": AnalysisConfig(**raw_config["analysis"]),
                "version": raw_config.get("version"),
                "environment": raw_config.get("environment"),
            }
        except Exception as e:
            raise RuntimeError(
                f"Invalid configuration format: {e} - NO FALLBACKS ALLOWED"
            )

    @property
    def models(self) -> Dict[str, ModelConfig]:
        """Get model configurations"""
        return self._config["models"]

    @property
    def openai_api(self) -> APIConfig:
        """Get OpenAI API configuration"""
        return self._config["openai_api"]

    @property
    def execution(self) -> ExecutionConfig:
        """Get execution configuration"""
        return self._config["execution"]

    @property
    def reasoning(self) -> ReasoningConfig:
        """Get reasoning configuration"""
        return self._config["reasoning"]

    @property
    def synthesis(self) -> SynthesisConfig:
        """Get synthesis configuration"""
        return self._config["synthesis"]

    @property
    def information_completion(self) -> InformationCompletionConfig:
        """Get information completion configuration"""
        return self._config["information_completion"]

    @property
    def validation(self) -> ValidationConfig:
        """Get validation configuration"""
        return self._config["validation"]

    @property
    def tools(self) -> ToolsConfig:
        """Get tools configuration"""
        return self._config["tools"]

    @property
    def agent_factory(self) -> AgentFactoryConfig:
        """Get agent factory configuration"""
        return self._config["agent_factory"]

    @property
    def file_processing(self) -> FileProcessingConfig:
        """Get file processing configuration"""
        return self._config["file_processing"]

    @property
    def complexity(self) -> ComplexityConfig:
        """Get complexity configuration"""
        return self._config["complexity"]

    @property
    def content_limits(self) -> ContentLimitsConfig:
        """Get content limits configuration"""
        return self._config["content_limits"]

    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration"""
        return self._config["logging"]

    @property
    def quality(self) -> QualityConfig:
        """Get quality configuration"""
        return self._config["quality"]

    @property
    def enforcement(self) -> EnforcementConfig:
        """Get enforcement configuration"""
        return self._config["enforcement"]

    @property
    def version(self) -> str:
        """Get configuration version"""
        return self._config["version"]

    @property
    def environment(self) -> str:
        """Get environment"""
        return self._config["environment"]

    @property
    def constants(self) -> ConstantsConfig:
        """Get system constants"""
        return self._config["constants"]

    @property
    def defaults(self) -> DefaultsConfig:
        """Get default values"""
        return self._config["defaults"]

    @property
    def patterns(self) -> PatternsConfig:
        """Get regex patterns"""
        return self._config["patterns"]

    @property
    def messages(self) -> MessagesConfig:
        """Get message templates"""
        return self._config["messages"]

    @property
    def error_messages(self) -> ErrorMessagesConfig:
        """Get error message templates"""
        return self._config["error_messages"]

    @property
    def status_values(self) -> StatusValuesConfig:
        """Get status value constants"""
        return self._config["status_values"]

    @property
    def analysis(self) -> AnalysisConfig:
        """Get analysis configuration"""
        return self._config["analysis"]

    def get_model_config(self, model_type: str) -> ModelConfig:
        """Get specific model configuration"""
        if model_type not in self.models:
            raise RuntimeError(
                f"Unknown model type: {model_type} - NO FALLBACKS ALLOWED"
            )
        return self.models[model_type]

    def get_constant(self, category: str, key: str) -> str:
        """Get a specific constant value"""
        category_data = getattr(self.constants, category, None)
        if not category_data:
            raise RuntimeError(
                f"Unknown constant category: {category} - NO FALLBACKS ALLOWED"
            )

        if isinstance(category_data, dict):
            if key not in category_data:
                raise RuntimeError(
                    f"Unknown constant key {key} in category {category} - NO FALLBACKS ALLOWED"
                )
            return category_data[key]

        # Handle nested dictionaries like ui.colors.red
        if hasattr(category_data, key):
            return getattr(category_data, key)

        raise RuntimeError(
            f"Unknown constant key {key} in category {category} - NO FALLBACKS ALLOWED"
        )

    def get_default(self, category: str, key: str) -> str:
        """Get a specific default value"""
        category_data = getattr(self.defaults, category, None)
        if not category_data:
            raise RuntimeError(
                f"Unknown default category: {category} - NO FALLBACKS ALLOWED"
            )

        if key not in category_data:
            raise RuntimeError(
                f"Unknown default key {key} in category {category} - NO FALLBACKS ALLOWED"
            )
        return category_data[key]

    def get_pattern(self, category: str, key: str) -> str:
        """Get a specific regex pattern"""
        category_data = getattr(self.patterns, category, None)
        if not category_data:
            raise RuntimeError(
                f"Unknown pattern category: {category} - NO FALLBACKS ALLOWED"
            )

        if key not in category_data:
            raise RuntimeError(
                f"Unknown pattern key {key} in category {category} - NO FALLBACKS ALLOWED"
            )
        return category_data[key]

    def get_message_template(self, category: str, key: str) -> str:
        """Get a specific message template"""
        category_data = getattr(self.messages, category, None)
        if not category_data:
            raise RuntimeError(
                f"Unknown message category: {category} - NO FALLBACKS ALLOWED"
            )

        if key not in category_data:
            raise RuntimeError(
                f"Unknown message key {key} in category {category} - NO FALLBACKS ALLOWED"
            )
        return category_data[key]


# Global configuration instance
config = ConfigManager()
