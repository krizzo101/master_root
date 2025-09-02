"""Orchestrator state management"""

from dataclasses import dataclass
from typing import Any, Dict, List

from ..utils.enhanced_logging import get_logger

logger = get_logger(__name__)


@dataclass
class OrchestratorState:
    """Central state for orchestration"""

    task_id: str = ""
    tasks: List[Dict[str, Any]] = None
    agents: List[Any] = None
    results: Dict[str, Any] = None
    status: str = "pending"
    errors: List[str] = None

    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []
        if self.agents is None:
            self.agents = []
        if self.results is None:
            self.results = {}
        if self.errors is None:
            self.errors = []
