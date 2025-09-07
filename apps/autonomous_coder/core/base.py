"""Base classes and data structures for the Autonomous Coder system."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from enum import Enum
import json


class ProjectType(Enum):
    """Types of projects the system can build."""
    SIMPLE_APP = "simple_app"
    WEB_APP = "web_app"
    REST_API = "rest_api"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    DASHBOARD = "dashboard"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    MICROSERVICE = "microservice"
    FULLSTACK = "fullstack"


@dataclass
class TechInfo:
    """Information about a technology/package."""
    name: str
    version: str
    latest_stable: str
    release_date: Optional[datetime] = None
    deprecations: List[str] = None
    best_practices: List[str] = None
    compatibility: Dict[str, str] = None
    documentation_url: Optional[str] = None
    
    def __post_init__(self):
        if self.deprecations is None:
            self.deprecations = []
        if self.best_practices is None:
            self.best_practices = []
        if self.compatibility is None:
            self.compatibility = {}


@dataclass
class BuildRequest:
    """Request to build a project."""
    description: str
    output_path: Path = Path("./output")
    constraints: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    force_research: bool = True
    interactive: bool = False
    
    def __post_init__(self):
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)


@dataclass
class BuildResult:
    """Result of a build operation."""
    success: bool
    project_path: Path
    tech_stack: Dict[str, str]
    files_created: List[str]
    execution_time: float
    errors: List[str] = None
    warnings: List[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metrics is None:
            self.metrics = {}
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            'success': self.success,
            'project_path': str(self.project_path),
            'tech_stack': self.tech_stack,
            'files_created': self.files_created,
            'execution_time': self.execution_time,
            'errors': self.errors,
            'warnings': self.warnings,
            'metrics': self.metrics
        }, indent=2)


@dataclass
class Requirements:
    """Parsed project requirements."""
    project_type: ProjectType
    features: List[str]
    complexity: str  # simple, medium, complex
    estimated_time: int  # minutes
    tech_preferences: Dict[str, str]
    constraints: List[str]


class BaseModule:
    """Base class for all system modules."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the module with optional configuration."""
        self.config = config or {}
        self.logger = self._setup_logging()
        self.metrics = {}
        
    def _setup_logging(self):
        """Set up logging for the module."""
        import logging
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message."""
        getattr(self.logger, level.lower())(message)
    
    def track_metric(self, name: str, value: Any):
        """Track a metric."""
        self.metrics[name] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all tracked metrics."""
        return self.metrics.copy()