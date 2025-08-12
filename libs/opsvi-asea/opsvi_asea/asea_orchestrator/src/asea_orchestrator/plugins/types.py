from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class PluginConfig:
    # Details for plugin configuration
    name: str
    version: str = "1.0.0"
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    # Context for plugin execution
    workflow_id: str
    task_id: str
    state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginResult:
    # Result of a plugin execution
    success: bool
    data: Any = None
    error_message: str = None


@dataclass
class Capability:
    # Describes a plugin's capability
    name: str
    description: str


@dataclass
class ValidationResult:
    # Result of input validation
    is_valid: bool
    errors: List[str] = field(default_factory=list)


@dataclass
class HealthStatus:
    # Health status of a plugin
    status: str = "OK"  # e.g., 'OK', 'DEGRADED', 'ERROR'
    details: str = ""


@dataclass
class Event:
    # Represents a system event
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
