#!/usr/bin/env python3
"""
DPO Enhancement Configuration

Control how much intelligence and enhancement DPO applies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class EnhancementLevel(Enum):
    """Different levels of DPO enhancement."""

    OFF = "off"  # Level 0: DPO disabled - orchestrator runs normally
    MINIMAL = "minimal"  # Level 1: Just parse and validate requests
    ESSENTIAL = "essential"  # Level 2: Add only what's needed for success (DEFAULT)
    BALANCED = "balanced"  # Level 3: Reasonable enhancements
    COMPREHENSIVE = "comprehensive"  # Level 4: Full analysis and enhancement
    MAXIMUM = "maximum"  # Level 5: Everything DPO can think of

    @classmethod
    def from_number(cls, num: int) -> "EnhancementLevel":
        """Get enhancement level from 0-5 scale."""
        levels = [
            cls.OFF,
            cls.MINIMAL,
            cls.ESSENTIAL,
            cls.BALANCED,
            cls.COMPREHENSIVE,
            cls.MAXIMUM,
        ]
        if 0 <= num < len(levels):
            return levels[num]
        return cls.ESSENTIAL  # Default to level 2

    def to_number(self) -> int:
        """Convert to 0-5 scale."""
        levels = {
            self.OFF: 0,
            self.MINIMAL: 1,
            self.ESSENTIAL: 2,
            self.BALANCED: 3,
            self.COMPREHENSIVE: 4,
            self.MAXIMUM: 5,
        }
        return levels.get(self, 2)


class EnhancementScope(Enum):
    """What aspects DPO should enhance."""

    AGENTS = "agents"  # Agent selection
    TASKS = "tasks"  # Task generation
    DEPENDENCIES = "dependencies"  # Dependency management
    QUALITY = "quality"  # Quality gates
    CONTEXT = "context"  # Context enrichment
    TESTING = "testing"  # Test coverage
    DOCUMENTATION = "documentation"  # Doc generation
    DEPLOYMENT = "deployment"  # Deployment setup
    MONITORING = "monitoring"  # Observability
    SECURITY = "security"  # Security hardening


@dataclass
class DPOEnhancementConfig:
    """Configuration for DPO enhancement behavior."""

    # Master switch
    enabled: bool = False  # OFF by default - must opt-in!

    # Enhancement level
    level: EnhancementLevel = EnhancementLevel.BALANCED

    # What to enhance (if None, use defaults for level)
    scopes: Optional[List[EnhancementScope]] = None

    # Specific controls
    max_agents: int = 10  # Don't go crazy with agents
    max_tasks_per_phase: int = 5  # Keep phases manageable
    add_quality_gates: bool = True  # Add quality checks
    add_documentation: bool = True  # Generate docs
    add_testing: bool = True  # Add test tasks
    infer_requirements: bool = False  # Guess missing requirements
    add_best_practices: bool = True  # Include industry standards

    # "Sturdy box" mode - just what's needed for success
    sturdy_box_mode: bool = False

    def get_scopes_for_level(self) -> List[EnhancementScope]:
        """Get appropriate scopes for enhancement level."""
        if self.scopes:
            return self.scopes

        if self.sturdy_box_mode:
            # Sturdy box = essential only
            return [
                EnhancementScope.AGENTS,
                EnhancementScope.TASKS,
                EnhancementScope.DEPENDENCIES,
                EnhancementScope.QUALITY,
                EnhancementScope.TESTING,
            ]

        level_scopes = {
            EnhancementLevel.OFF: [],
            EnhancementLevel.MINIMAL: [EnhancementScope.AGENTS, EnhancementScope.TASKS],
            EnhancementLevel.ESSENTIAL: [
                EnhancementScope.AGENTS,
                EnhancementScope.TASKS,
                EnhancementScope.DEPENDENCIES,
                EnhancementScope.QUALITY,
            ],
            EnhancementLevel.BALANCED: [
                EnhancementScope.AGENTS,
                EnhancementScope.TASKS,
                EnhancementScope.DEPENDENCIES,
                EnhancementScope.QUALITY,
                EnhancementScope.CONTEXT,
                EnhancementScope.TESTING,
                EnhancementScope.DOCUMENTATION,
            ],
            EnhancementLevel.COMPREHENSIVE: [
                EnhancementScope.AGENTS,
                EnhancementScope.TASKS,
                EnhancementScope.DEPENDENCIES,
                EnhancementScope.QUALITY,
                EnhancementScope.CONTEXT,
                EnhancementScope.TESTING,
                EnhancementScope.DOCUMENTATION,
                EnhancementScope.DEPLOYMENT,
                EnhancementScope.SECURITY,
            ],
            EnhancementLevel.MAXIMUM: list(EnhancementScope),  # Everything
        }

        return level_scopes.get(self.level, [])

    def should_enhance(self, scope: EnhancementScope) -> bool:
        """Check if a specific scope should be enhanced."""
        if not self.enabled:
            return False
        return scope in self.get_scopes_for_level()

    def dial(self, level: int) -> "DPOEnhancementConfig":
        """Dial enhancement up or down (0-5 scale)."""
        self.level = EnhancementLevel.from_number(level)
        self.enabled = level > 0

        # Adjust other settings based on level
        if level == 0:
            self.enabled = False
        elif level == 1:  # Minimal
            self.max_agents = 3
            self.max_tasks_per_phase = 2
            self.add_documentation = False
            self.add_best_practices = False
        elif level == 2:  # Essential
            self.max_agents = 6
            self.max_tasks_per_phase = 4
            self.add_documentation = False
            self.add_best_practices = True
        elif level == 3:  # Balanced
            self.max_agents = 8
            self.max_tasks_per_phase = 4
            self.add_documentation = True
            self.add_best_practices = True
        elif level == 4:  # Comprehensive
            self.max_agents = 12
            self.max_tasks_per_phase = 6
            self.add_documentation = True
            self.add_best_practices = True
            self.infer_requirements = False
        elif level >= 5:  # Maximum
            self.max_agents = 15
            self.max_tasks_per_phase = 8
            self.add_documentation = True
            self.add_best_practices = True
            self.infer_requirements = True

        return self

    @classmethod
    def sturdy_box(cls) -> "DPOEnhancementConfig":
        """Create a 'sturdy box' config - just what's needed for success."""
        return cls(
            enabled=True,
            level=EnhancementLevel.ESSENTIAL,
            sturdy_box_mode=True,
            max_agents=5,
            max_tasks_per_phase=3,
            add_quality_gates=True,
            add_documentation=False,  # Skip unless needed
            add_testing=True,
            infer_requirements=False,  # Don't guess
            add_best_practices=False,  # Keep it simple
        )

    @classmethod
    def smart_default(cls) -> "DPOEnhancementConfig":
        """Create a balanced default config."""
        return cls(
            enabled=True,
            level=EnhancementLevel.BALANCED,
            sturdy_box_mode=False,
            max_agents=8,
            max_tasks_per_phase=4,
            add_quality_gates=True,
            add_documentation=True,
            add_testing=True,
            infer_requirements=False,
            add_best_practices=True,
        )

    @classmethod
    def maximum_enhancement(cls) -> "DPOEnhancementConfig":
        """Create config for maximum enhancement (the crazy cool stuff)."""
        return cls(
            enabled=True,
            level=EnhancementLevel.MAXIMUM,
            sturdy_box_mode=False,
            max_agents=15,
            max_tasks_per_phase=8,
            add_quality_gates=True,
            add_documentation=True,
            add_testing=True,
            infer_requirements=True,  # Yes, guess what they need
            add_best_practices=True,
        )

    @classmethod
    def from_string(cls, config_str: str) -> "DPOEnhancementConfig":
        """Create config from string like 'sturdy', 'smart', 'max', 'off'."""
        configs = {
            "off": cls(enabled=False),
            "sturdy": cls.sturdy_box(),
            "smart": cls.smart_default(),
            "balanced": cls.smart_default(),
            "max": cls.maximum_enhancement(),
            "maximum": cls.maximum_enhancement(),
            "minimal": cls(enabled=True, level=EnhancementLevel.MINIMAL),
            "essential": cls(enabled=True, level=EnhancementLevel.ESSENTIAL),
            "comprehensive": cls(enabled=True, level=EnhancementLevel.COMPREHENSIVE),
        }
        return configs.get(config_str.lower(), cls.smart_default())


# Default configuration presets
PRESETS = {
    "off": DPOEnhancementConfig(enabled=False),
    "sturdy": DPOEnhancementConfig.sturdy_box(),
    "smart": DPOEnhancementConfig.smart_default(),
    "max": DPOEnhancementConfig.maximum_enhancement(),
}

# Global default - ON at Essential level (smart but not excessive)
DEFAULT_CONFIG = DPOEnhancementConfig(
    enabled=True,
    level=EnhancementLevel.ESSENTIAL,  # Level 2-3: smart defaults
    max_agents=6,
    max_tasks_per_phase=4,
    add_quality_gates=True,
    add_documentation=False,  # Can be enabled if needed
    add_testing=True,
    infer_requirements=False,
    add_best_practices=True,
)
