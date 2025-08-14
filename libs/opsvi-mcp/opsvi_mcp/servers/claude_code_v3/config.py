"""Enhanced configuration for Claude Code V3"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class AdaptiveRecursionLimits:
    """Enhanced recursion control with adaptive limits"""

    # Increased depth for better decomposition
    max_depth: int = 5

    # Dynamic concurrency based on depth
    concurrency_by_depth: Dict[int, int] = field(
        default_factory=lambda: {
            0: 10,  # Root level - high parallelism
            1: 8,  # First sub-level
            2: 6,  # Second sub-level
            3: 4,  # Third sub-level
            4: 2,  # Fourth sub-level
            5: 1,  # Deepest level - sequential
        }
    )

    # Adaptive limits
    adaptive_scaling: bool = True
    min_concurrency: int = 2
    max_total_jobs: int = 50

    # Priority scheduling
    enable_priority_queue: bool = True
    high_priority_reserved: int = 2

    # Recovery settings
    enable_checkpointing: bool = True
    checkpoint_interval: int = 60000  # 1 minute

    def get_concurrency_for_depth(self, depth: int) -> int:
        """Get concurrency limit for given depth"""
        return self.concurrency_by_depth.get(depth, 2)


@dataclass
class TimeoutConfig:
    """Dynamic timeout configuration"""

    base_timeout: int = 300000  # 5 minutes
    max_timeout: int = 1800000  # 30 minutes

    # Multipliers for complexity
    complexity_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "simple": 1.0,
            "moderate": 2.0,
            "complex": 3.0,
            "very_complex": 5.0,
        }
    )

    # Depth multiplier
    depth_multiplier: float = 1.5

    # Adaptive timeout
    enable_adaptive: bool = True
    learning_enabled: bool = True

    def calculate_timeout(
        self, complexity: str, depth: int, file_count: int = 1
    ) -> int:
        """Calculate timeout based on task complexity"""
        base = self.base_timeout
        depth_mult = self.depth_multiplier**depth
        complexity_mult = self.complexity_multipliers.get(complexity, 2.0)
        file_mult = 1 + (file_count * 0.2)

        timeout = int(base * depth_mult * complexity_mult * file_mult)
        return min(timeout, self.max_timeout)


@dataclass
class TaskDecompositionConfig:
    """Task decomposition settings"""

    enable_decomposition: bool = True
    max_subtasks: int = 10
    parallel_threshold: int = 3  # Min subtasks for parallel execution

    # Task patterns for decomposition
    decomposition_patterns: Dict[str, list] = field(
        default_factory=lambda: {
            "server_creation": [
                "structure",
                "config",
                "models",
                "server",
                "tools",
                "tests",
            ],
            "multi_file": ["analyze", "plan", "execute", "verify"],
            "refactoring": ["analyze", "backup", "refactor", "test", "cleanup"],
        }
    )


@dataclass
class ResourceManagementConfig:
    """Resource management settings"""

    enable_adaptive_resources: bool = True
    cpu_threshold_high: float = 80.0
    cpu_threshold_low: float = 40.0
    memory_threshold_mb: int = 1024

    # Job metrics
    track_performance: bool = True
    history_size: int = 100

    # Resource limits
    max_memory_per_job: int = 512  # MB
    max_cpu_per_job: float = 25.0  # Percentage


@dataclass
class RecoveryConfig:
    """Recovery and resilience settings"""

    enable_recovery: bool = True
    max_retry_attempts: int = 3
    retry_delay_ms: int = 5000

    # Partial completion thresholds
    salvage_threshold: float = 0.7  # 70% complete
    checkpoint_threshold: float = 0.3  # 30% complete

    # Recovery strategies
    timeout_multiplier: float = 2.0
    decompose_on_failure: bool = True
    reduce_scope_on_failure: bool = True


@dataclass
class EnhancedConfig:
    """Main enhanced configuration for Claude Code V3"""

    # Core settings
    claude_code_token: Optional[str] = None

    # Enhanced components
    recursion: AdaptiveRecursionLimits = field(default_factory=AdaptiveRecursionLimits)
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    decomposition: TaskDecompositionConfig = field(
        default_factory=TaskDecompositionConfig
    )
    resources: ResourceManagementConfig = field(
        default_factory=ResourceManagementConfig
    )
    recovery: RecoveryConfig = field(default_factory=RecoveryConfig)

    # Logging
    log_level: str = "INFO"
    logs_dir: str = "/home/opsvi/master_root/logs/claude-code-v3"
    enable_trace: bool = True

    def __post_init__(self):
        """Load from environment variables"""

        # Token
        if not self.claude_code_token:
            self.claude_code_token = os.getenv("CLAUDE_CODE_TOKEN")

        # Recursion depth
        if os.getenv("CLAUDE_MAX_RECURSION_DEPTH"):
            self.recursion.max_depth = int(os.getenv("CLAUDE_MAX_RECURSION_DEPTH"))

        # Adaptive concurrency
        if os.getenv("CLAUDE_ADAPTIVE_CONCURRENCY"):
            self.recursion.adaptive_scaling = (
                os.getenv("CLAUDE_ADAPTIVE_CONCURRENCY") == "true"
            )

        # Load concurrency by depth
        for i in range(6):
            env_key = f"CLAUDE_BASE_CONCURRENCY_D{i}"
            if os.getenv(env_key):
                self.recursion.concurrency_by_depth[i] = int(os.getenv(env_key))

        # Timeout settings
        if os.getenv("CLAUDE_ENABLE_ADAPTIVE_TIMEOUT"):
            self.timeout.enable_adaptive = (
                os.getenv("CLAUDE_ENABLE_ADAPTIVE_TIMEOUT") == "true"
            )

        if os.getenv("CLAUDE_BASE_TIMEOUT"):
            self.timeout.base_timeout = int(os.getenv("CLAUDE_BASE_TIMEOUT"))

        if os.getenv("CLAUDE_MAX_TIMEOUT"):
            self.timeout.max_timeout = int(os.getenv("CLAUDE_MAX_TIMEOUT"))

        # Decomposition
        if os.getenv("CLAUDE_ENABLE_TASK_DECOMPOSITION"):
            self.decomposition.enable_decomposition = (
                os.getenv("CLAUDE_ENABLE_TASK_DECOMPOSITION") == "true"
            )

        # Checkpointing
        if os.getenv("CLAUDE_ENABLE_CHECKPOINTING"):
            self.recursion.enable_checkpointing = (
                os.getenv("CLAUDE_ENABLE_CHECKPOINTING") == "true"
            )

        # Recovery
        if os.getenv("CLAUDE_ENABLE_RECOVERY"):
            self.recovery.enable_recovery = (
                os.getenv("CLAUDE_ENABLE_RECOVERY") == "true"
            )

        # Learning
        if os.getenv("CLAUDE_ENABLE_LEARNING"):
            self.timeout.learning_enabled = (
                os.getenv("CLAUDE_ENABLE_LEARNING") == "true"
            )


# Global configuration instance
config = EnhancedConfig()
