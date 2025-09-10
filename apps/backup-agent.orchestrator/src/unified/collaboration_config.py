#!/usr/bin/env python3
"""
Collaboration Configuration Module
Configuration dataclasses and settings for the collaboration system
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ExecutionMode(Enum):
    """Execution modes for collaborative orchestration"""

    TRADITIONAL = "traditional"  # No collaboration
    SHARED = "shared"  # Simultaneous work on shared tasks
    HANDOFF = "handoff"  # Sequential task handoff
    REVIEW = "review"  # Work review before completion
    HYBRID = "hybrid"  # Mix of collaborative and independent


class TeamFormationMode(Enum):
    """Team formation strategies"""

    AUTO = "auto"  # Automatic based on capabilities
    MANUAL = "manual"  # Manually specified teams
    SKILL_BASED = "skill_based"  # Based on skill matching
    PERFORMANCE_BASED = "performance_based"  # Based on performance scores
    LOAD_BALANCED = "load_balanced"  # Balance workload across agents


class MessagePriority(Enum):
    """Message priority levels"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3
    CRITICAL = 4


@dataclass
class CollaborationConfig:
    """Main configuration for collaborative execution"""

    # Core features (31/35 fully working)
    enable_messaging: bool = True
    enable_shared_workspace: bool = True
    enable_team_formation: bool = True
    enable_real_time_sync: bool = True
    enable_event_logging: bool = True

    # Execution settings
    execution_mode: str = "hybrid"
    team_formation_mode: str = "auto"

    # Team settings
    max_team_size: int = 10
    min_team_size: int = 1
    auto_team_threshold: float = 0.7  # Minimum capability match for auto-team

    # Messaging settings
    message_retention_hours: int = 24
    max_message_queue_size: int = 1000
    message_batch_size: int = 10
    enable_message_persistence: bool = True
    default_message_priority: int = MessagePriority.NORMAL.value

    # Workspace settings
    workspace_sync_interval: float = 1.0  # seconds
    workspace_file_limit: int = 1000
    workspace_size_limit_mb: int = 500
    enable_workspace_versioning: bool = True
    workspace_cleanup_hours: int = 72

    # Collaboration timeouts
    collaboration_timeout: float = 300.0  # seconds
    message_timeout: float = 30.0
    workspace_lock_timeout: float = 10.0
    team_formation_timeout: float = 60.0

    # Performance settings
    parallel_team_operations: bool = True
    max_parallel_teams: int = 5
    agent_pool_size: int = 50

    # Monitoring settings
    enable_metrics: bool = True
    metrics_interval: float = 5.0
    enable_health_checks: bool = True
    health_check_interval: float = 30.0


@dataclass
class AgentConfig:
    """Configuration for individual agents"""

    agent_id: str
    agent_type: str = "generic"

    # Capabilities
    skills: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    supported_languages: List[str] = field(default_factory=lambda: ["python"])

    # Performance settings
    max_concurrent_tasks: int = 3
    task_timeout: float = 120.0
    retry_attempts: int = 2

    # Collaboration preferences
    preferred_team_size: int = 3
    collaboration_style: str = "cooperative"  # cooperative, independent, leader
    communication_style: str = "verbose"  # verbose, concise, silent

    # Resource limits
    max_memory_mb: int = 1024
    max_cpu_percent: float = 80.0
    max_tokens: int = 100000

    # Scoring weights
    performance_weight: float = 0.4
    availability_weight: float = 0.3
    collaboration_weight: float = 0.3


@dataclass
class TaskCollaborationConfig:
    """Configuration for task-level collaboration"""

    task_id: str
    collaboration_enabled: bool = True

    # Execution mode override
    execution_mode: Optional[str] = None

    # Team requirements
    required_capabilities: List[str] = field(default_factory=list)
    preferred_team_size: int = 3
    allow_partial_team: bool = True

    # Workspace settings
    require_shared_workspace: bool = True
    workspace_permissions: Dict[str, List[str]] = field(default_factory=dict)

    # Communication settings
    enable_broadcast: bool = False
    message_types: List[str] = field(
        default_factory=lambda: ["general", "status", "result"]
    )

    # Coordination settings
    require_consensus: bool = False
    min_consensus_agents: int = 2
    handoff_strategy: str = "sequential"  # sequential, parallel, conditional

    # Review settings
    require_review: bool = False
    review_agents: List[str] = field(default_factory=list)
    review_threshold: float = 0.8


@dataclass
class WorkspaceConfig:
    """Configuration for shared workspaces"""

    workspace_id: str
    workspace_type: str = "general"  # general, code, data, documentation

    # Access control
    owner_agent: str = "system"
    default_permissions: List[str] = field(default_factory=lambda: ["read", "write"])

    # Storage settings
    max_files: int = 100
    max_file_size_mb: int = 10
    allowed_extensions: List[str] = field(
        default_factory=lambda: [".py", ".json", ".txt", ".md"]
    )

    # Synchronization
    sync_strategy: str = "immediate"  # immediate, batch, periodic
    sync_batch_size: int = 10
    conflict_resolution: str = "last_write_wins"  # last_write_wins, merge, manual

    # Versioning
    enable_versioning: bool = True
    max_versions: int = 10
    version_retention_days: int = 7

    # Cleanup
    auto_cleanup: bool = True
    cleanup_after_hours: int = 24
    archive_on_cleanup: bool = True


@dataclass
class MessageBusConfig:
    """Configuration for the message bus system"""

    # Transport settings
    transport_type: str = "memory"  # memory, file, redis, rabbitmq
    persistence_enabled: bool = True

    # Queue settings
    max_queue_size: int = 10000
    queue_overflow_strategy: str = "drop_oldest"  # drop_oldest, drop_newest, block

    # Delivery settings
    delivery_mode: str = "at_least_once"  # at_most_once, at_least_once, exactly_once
    retry_policy: Dict[str, Any] = field(
        default_factory=lambda: {
            "max_retries": 3,
            "retry_delay": 1.0,
            "backoff_multiplier": 2.0,
        }
    )

    # Routing
    enable_topics: bool = True
    enable_routing_keys: bool = True
    enable_wildcards: bool = True

    # Performance
    batch_processing: bool = True
    batch_size: int = 100
    batch_timeout: float = 1.0

    # Monitoring
    enable_message_tracking: bool = True
    enable_dead_letter_queue: bool = True
    message_ttl_seconds: int = 3600


@dataclass
class MetricsConfig:
    """Configuration for metrics and monitoring"""

    # Collection settings
    enable_metrics: bool = True
    collection_interval: float = 5.0

    # Agent metrics
    track_agent_performance: bool = True
    track_agent_availability: bool = True
    track_agent_collaboration: bool = True

    # Task metrics
    track_task_duration: bool = True
    track_task_success_rate: bool = True
    track_task_dependencies: bool = True

    # Collaboration metrics
    track_team_formation: bool = True
    track_message_volume: bool = True
    track_workspace_usage: bool = True

    # Export settings
    export_format: str = "json"  # json, csv, prometheus
    export_interval: float = 60.0
    export_path: str = "metrics"

    # Alerting
    enable_alerts: bool = True
    alert_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "agent_failure_rate": 0.2,
            "task_timeout_rate": 0.1,
            "message_queue_overflow": 0.9,
            "workspace_size_limit": 0.8,
        }
    )


class CollaborationConfigBuilder:
    """Builder for creating collaboration configurations"""

    @staticmethod
    def create_default() -> CollaborationConfig:
        """Create default collaboration configuration"""
        return CollaborationConfig()

    @staticmethod
    def create_minimal() -> CollaborationConfig:
        """Create minimal configuration for basic collaboration"""
        return CollaborationConfig(
            enable_messaging=True,
            enable_shared_workspace=False,
            enable_team_formation=False,
            execution_mode="traditional",
            max_team_size=1,
        )

    @staticmethod
    def create_full_collaboration() -> CollaborationConfig:
        """Create configuration with all collaboration features enabled"""
        return CollaborationConfig(
            enable_messaging=True,
            enable_shared_workspace=True,
            enable_team_formation=True,
            enable_real_time_sync=True,
            enable_event_logging=True,
            execution_mode="shared",
            team_formation_mode="skill_based",
            max_team_size=20,
            parallel_team_operations=True,
        )

    @staticmethod
    def create_handoff_mode() -> CollaborationConfig:
        """Create configuration for handoff execution mode"""
        return CollaborationConfig(
            enable_messaging=True,
            enable_shared_workspace=True,
            enable_team_formation=True,
            execution_mode="handoff",
            team_formation_mode="manual",
            parallel_team_operations=False,
        )

    @staticmethod
    def create_review_mode() -> CollaborationConfig:
        """Create configuration for review execution mode"""
        return CollaborationConfig(
            enable_messaging=True,
            enable_shared_workspace=True,
            enable_team_formation=True,
            execution_mode="review",
            team_formation_mode="skill_based",
        )

    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> CollaborationConfig:
        """Create configuration from dictionary"""
        config = CollaborationConfig()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


def get_execution_mode_description(mode: ExecutionMode) -> str:
    """Get detailed description of execution mode"""
    descriptions = {
        ExecutionMode.TRADITIONAL: (
            "Traditional mode: Agents work independently without collaboration. "
            "No messaging or shared workspaces. Maximum parallelism."
        ),
        ExecutionMode.SHARED: (
            "Shared mode: Agents work simultaneously on shared tasks. "
            "Full messaging and workspace sharing. Real-time synchronization."
        ),
        ExecutionMode.HANDOFF: (
            "Handoff mode: Sequential task execution with handoff between agents. "
            "Each agent completes their part and passes to the next."
        ),
        ExecutionMode.REVIEW: (
            "Review mode: Work is reviewed by other agents before completion. "
            "Ensures quality through peer review process."
        ),
        ExecutionMode.HYBRID: (
            "Hybrid mode: Intelligent mix of collaborative and independent execution. "
            "Adapts based on task requirements and agent availability."
        ),
    }
    return descriptions.get(mode, "Unknown execution mode")


def validate_config(config: CollaborationConfig) -> List[str]:
    """Validate collaboration configuration and return any issues"""
    issues = []

    # Validate team size
    if config.max_team_size < config.min_team_size:
        issues.append("max_team_size must be >= min_team_size")

    # Validate execution mode
    if config.execution_mode not in [m.value for m in ExecutionMode]:
        issues.append(f"Invalid execution_mode: {config.execution_mode}")

    # Validate team formation mode
    if config.team_formation_mode not in [m.value for m in TeamFormationMode]:
        issues.append(f"Invalid team_formation_mode: {config.team_formation_mode}")

    # Validate timeouts
    if config.collaboration_timeout <= 0:
        issues.append("collaboration_timeout must be positive")

    # Validate workspace settings
    if config.workspace_sync_interval <= 0:
        issues.append("workspace_sync_interval must be positive")

    # Validate parallel settings
    if config.max_parallel_teams <= 0:
        issues.append("max_parallel_teams must be positive")

    return issues
