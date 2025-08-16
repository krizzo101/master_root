"""
Smart Decomposition Meta-Intelligence System - Configuration Management
OpenAI-Exclusive Implementation with Structured Response Enforcement
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ModelType(Enum):
    """OpenAI model types for strategic allocation"""

    O3_REASONING = "o3"  # Complex planning and reasoning
    O3_MINI = "o3-mini"  # Fast reasoning tasks
    GPT41_IMPLEMENTATION = "gpt-4.1"  # Code generation and implementation
    GPT41_MINI = "gpt-4.1-mini"  # Efficient tasks
    GPT41_NANO = "gpt-4.1-nano"  # Fast responses


class AgentRole(Enum):
    """Agent roles in the Smart Decomposition system"""

    MANAGER = "manager"
    REQUIREMENTS_EXPANDER = "requirements_expander"
    WORK_DECOMPOSER = "work_decomposer"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    COORDINATOR = "coordinator"
    VALIDATOR = "validator"
    INTEGRATOR = "integrator"
    OPTIMIZER = "optimizer"


@dataclass
class ModelConfig:
    """OpenAI model configuration"""

    reasoning: str = ModelType.O3_REASONING.value
    reasoning_fast: str = ModelType.O3_MINI.value
    implementation: str = ModelType.GPT41_IMPLEMENTATION.value
    coordination: str = ModelType.GPT41_IMPLEMENTATION.value
    optimization: str = ModelType.GPT41_MINI.value
    fast_response: str = ModelType.GPT41_NANO.value


@dataclass
class StructuredResponseConfig:
    """Configuration for structured JSON responses"""

    enforce_json_schemas: bool = True
    response_validation: bool = True
    fallback_on_validation_error: bool = False
    max_retry_attempts: int = 3


@dataclass
class Neo4jConfig:
    """Neo4j database configuration"""

    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "password"
    database: str = "smart_decomposition_poc"


@dataclass
class ParallelExecutionConfig:
    """Parallel execution configuration"""

    max_parallel_agents: int = 5
    dependency_timeout_seconds: int = 300
    context_propagation_enabled: bool = True
    state_isolation_enabled: bool = True
    contamination_detection: bool = True


@dataclass
class PerformanceConfig:
    """Performance targets and limits"""

    parallel_efficiency_target: float = 3.0  # 3x improvement minimum
    agent_creation_time_limit: float = 5.0  # seconds
    memory_per_agent_limit: int = 512  # MB
    success_rate_target: float = 0.90  # 90%


@dataclass
class MCPToolsConfig:
    """MCP tools configuration"""

    web_search: dict[str, Any] = field(
        default_factory=lambda: {"enabled": True, "provider": "brave"}
    )
    knowledge_base: dict[str, Any] = field(
        default_factory=lambda: {"enabled": True, "provider": "neo4j"}
    )
    tech_docs: dict[str, Any] = field(
        default_factory=lambda: {"enabled": True, "provider": "context7"}
    )
    research_papers: dict[str, Any] = field(
        default_factory=lambda: {"enabled": True, "provider": "arxiv"}
    )


@dataclass
class SystemConfig:
    """Main system configuration"""

    name: str = "Smart Decomposition Meta-Intelligence POC"
    version: str = "1.0.0"
    environment: str = "development"

    # Component configurations
    models: ModelConfig = field(default_factory=ModelConfig)
    structured_responses: StructuredResponseConfig = field(
        default_factory=StructuredResponseConfig
    )
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    parallel_execution: ParallelExecutionConfig = field(
        default_factory=ParallelExecutionConfig
    )
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    mcp_tools: MCPToolsConfig = field(default_factory=MCPToolsConfig)

    # Agent model mapping
    agent_models: dict[str, str] = field(
        default_factory=lambda: {
            "manager": "reasoning",
            "requirements_expander": "reasoning",
            "work_decomposer": "reasoning",
            "architect": "reasoning",
            "developer": "implementation",
            "tester": "optimization",
            "coordinator": "coordination",
            "validator": "optimization",
            "integrator": "implementation",
            "optimizer": "optimization",
        }
    )


class ConfigManager:
    """Configuration manager for loading and accessing configuration"""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> str:
        """Get default configuration path"""
        return "config/smart_decomposition_poc/development/poc_config.yaml"

    def _load_config(self) -> SystemConfig:
        """Load configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                print(f"Configuration file not found: {self.config_path}")
                print("Using default configuration")
                return SystemConfig()

            with open(config_file) as f:
                yaml_config = yaml.safe_load(f)

            return self._yaml_to_config(yaml_config)

        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using default configuration")
            return SystemConfig()

    def _yaml_to_config(self, yaml_config: dict[str, Any]) -> SystemConfig:
        """Convert YAML configuration to SystemConfig object"""
        config = SystemConfig()

        # System settings
        if "system" in yaml_config:
            system = yaml_config["system"]
            config.name = system.get("name", config.name)
            config.version = system.get("version", config.version)
            config.environment = system.get("environment", config.environment)

        # Model configuration
        if "models" in yaml_config:
            models = yaml_config["models"]
            config.models = ModelConfig(
                reasoning=models.get("reasoning", config.models.reasoning),
                reasoning_fast=models.get(
                    "reasoning_fast", config.models.reasoning_fast
                ),
                implementation=models.get(
                    "implementation", config.models.implementation
                ),
                coordination=models.get("coordination", config.models.coordination),
                optimization=models.get("optimization", config.models.optimization),
                fast_response=models.get("fast_response", config.models.fast_response),
            )

        # Agent models mapping
        if "agent_models" in yaml_config:
            config.agent_models = yaml_config["agent_models"]

        # Structured responses
        if "structured_responses" in yaml_config:
            sr = yaml_config["structured_responses"]
            config.structured_responses = StructuredResponseConfig(
                enforce_json_schemas=sr.get("enforce_json_schemas", True),
                response_validation=sr.get("response_validation", True),
                fallback_on_validation_error=sr.get(
                    "fallback_on_validation_error", False
                ),
                max_retry_attempts=sr.get("max_retry_attempts", 3),
            )

        # Neo4j configuration
        if "neo4j" in yaml_config:
            neo4j = yaml_config["neo4j"]
            config.neo4j = Neo4jConfig(
                uri=neo4j.get("uri", config.neo4j.uri),
                username=neo4j.get("username", config.neo4j.username),
                password=neo4j.get("password", config.neo4j.password),
                database=neo4j.get("database", config.neo4j.database),
            )

        # Parallel execution
        if "parallel_execution" in yaml_config:
            pe = yaml_config["parallel_execution"]
            config.parallel_execution = ParallelExecutionConfig(
                max_parallel_agents=pe.get("max_parallel_agents", 5),
                dependency_timeout_seconds=pe.get("dependency_timeout_seconds", 300),
                context_propagation_enabled=pe.get("context_propagation_enabled", True),
                state_isolation_enabled=pe.get("state_isolation_enabled", True),
                contamination_detection=pe.get("contamination_detection", True),
            )

        # Performance configuration
        if "performance" in yaml_config:
            perf = yaml_config["performance"]
            config.performance = PerformanceConfig(
                parallel_efficiency_target=perf.get("parallel_efficiency_target", 3.0),
                agent_creation_time_limit=perf.get("agent_creation_time_limit", 5.0),
                memory_per_agent_limit=perf.get("memory_per_agent_limit", 512),
                success_rate_target=perf.get("success_rate_target", 0.90),
            )

        # MCP tools configuration
        if "mcp_tools" in yaml_config:
            tools = yaml_config["mcp_tools"]
            config.mcp_tools = MCPToolsConfig(
                web_search=tools.get(
                    "web_search", {"enabled": True, "provider": "brave"}
                ),
                knowledge_base=tools.get(
                    "knowledge_base", {"enabled": True, "provider": "neo4j"}
                ),
                tech_docs=tools.get(
                    "tech_docs", {"enabled": True, "provider": "context7"}
                ),
                research_papers=tools.get(
                    "research_papers", {"enabled": True, "provider": "arxiv"}
                ),
            )

        return config

    def get_model_for_role(self, role: AgentRole) -> str:
        """Get the appropriate OpenAI model for an agent role"""
        role_key = role.value if isinstance(role, AgentRole) else role
        model_type = self.config.agent_models.get(role_key, "optimization")

        model_mapping = {
            "reasoning": self.config.models.reasoning,
            "reasoning_fast": self.config.models.reasoning_fast,
            "implementation": self.config.models.implementation,
            "coordination": self.config.models.coordination,
            "optimization": self.config.models.optimization,
            "fast_response": self.config.models.fast_response,
        }

        return model_mapping.get(model_type, self.config.models.optimization)

    def get_config(self) -> SystemConfig:
        """Get the loaded configuration"""
        return self.config


# Global configuration instance
_config_manager: ConfigManager | None = None


def get_config() -> SystemConfig:
    """Get global configuration instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_config()


def get_model_for_role(role: AgentRole) -> str:
    """Get model for agent role using global configuration"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_model_for_role(role)
