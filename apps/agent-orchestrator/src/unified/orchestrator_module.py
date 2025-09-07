#!/usr/bin/env python3
"""
Base interface for orchestrator feature modules.
Allows modular composition of orchestrator capabilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from src.generic_orchestrator import GenericOrchestrator, AgentTask

logger = logging.getLogger(__name__)


@dataclass
class ModuleConfig:
    """Configuration for an orchestrator module"""
    
    enabled: bool = True
    priority: int = 0  # Lower number = higher priority
    required_dependencies: List[str] = None
    optional_dependencies: List[str] = None
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.required_dependencies is None:
            self.required_dependencies = []
        if self.optional_dependencies is None:
            self.optional_dependencies = []
        if self.config is None:
            self.config = {}


class OrchestratorModule(ABC):
    """
    Base class for orchestrator feature modules.
    Each module encapsulates a specific feature or capability.
    """
    
    def __init__(self, orchestrator: 'GenericOrchestrator', config: ModuleConfig = None):
        self.orchestrator = orchestrator
        self.config = config or ModuleConfig()
        self.initialized = False
        self._dependencies_validated = False
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique module name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Module description"""
        pass
    
    @property
    def version(self) -> str:
        """Module version"""
        return "1.0.0"
    
    def validate_dependencies(self) -> bool:
        """
        Validate that required dependencies are available.
        Returns True if all requirements are met.
        """
        if self._dependencies_validated:
            return True
            
        # Check required dependencies
        for dep in self.config.required_dependencies:
            try:
                __import__(dep)
            except ImportError:
                logger.error(f"{self.name} module missing required dependency: {dep}")
                return False
        
        # Check optional dependencies (just warn)
        for dep in self.config.optional_dependencies:
            try:
                __import__(dep)
            except ImportError:
                logger.warning(f"{self.name} module missing optional dependency: {dep}")
        
        self._dependencies_validated = True
        return True
    
    async def initialize(self) -> bool:
        """
        Initialize the module.
        Returns True if initialization successful.
        """
        if self.initialized:
            return True
            
        if not self.validate_dependencies():
            logger.error(f"Failed to initialize {self.name}: dependency validation failed")
            return False
            
        try:
            await self._initialize()
            self.initialized = True
            logger.info(f"Module {self.name} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {e}")
            return False
    
    @abstractmethod
    async def _initialize(self):
        """
        Module-specific initialization logic.
        Override in subclasses.
        """
        pass
    
    async def cleanup(self):
        """
        Cleanup module resources.
        Called when orchestrator shuts down.
        """
        if self.initialized:
            await self._cleanup()
            self.initialized = False
            logger.info(f"Module {self.name} cleaned up")
    
    async def _cleanup(self):
        """
        Module-specific cleanup logic.
        Override in subclasses if needed.
        """
        pass
    
    # Hook methods that modules can override
    
    async def pre_task_execution(self, task: 'AgentTask'):
        """Called before a task is executed"""
        pass
    
    async def post_task_execution(self, task: 'AgentTask'):
        """Called after a task is executed"""
        pass
    
    async def on_task_success(self, task: 'AgentTask'):
        """Called when a task completes successfully"""
        pass
    
    async def on_task_failure(self, task: 'AgentTask'):
        """Called when a task fails"""
        pass
    
    async def pre_batch_execution(self, tasks: List['AgentTask']):
        """Called before a batch of tasks is executed"""
        pass
    
    async def post_batch_execution(self, tasks: List['AgentTask'], results: List[Dict]):
        """Called after a batch of tasks is executed"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get module status information.
        """
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.config.enabled,
            "initialized": self.initialized,
            "priority": self.config.priority,
            "description": self.description
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get module-specific metrics.
        Override in subclasses to provide metrics.
        """
        return {}
    
    def validate_task(self, task: 'AgentTask') -> Optional[str]:
        """
        Validate a task according to module rules.
        Returns error message if validation fails, None if OK.
        """
        return None


class ModuleRegistry:
    """
    Registry for managing orchestrator modules.
    """
    
    def __init__(self):
        self.modules: Dict[str, OrchestratorModule] = {}
        self._initialization_order: List[str] = []
        
    def register(self, module: OrchestratorModule):
        """Register a module"""
        if module.name in self.modules:
            logger.warning(f"Module {module.name} already registered, replacing")
        
        self.modules[module.name] = module
        self._update_initialization_order()
        logger.info(f"Registered module: {module.name}")
    
    def unregister(self, name: str):
        """Unregister a module"""
        if name in self.modules:
            del self.modules[name]
            self._update_initialization_order()
            logger.info(f"Unregistered module: {name}")
    
    def get(self, name: str) -> Optional[OrchestratorModule]:
        """Get a module by name"""
        return self.modules.get(name)
    
    def list_modules(self) -> List[str]:
        """List all registered module names"""
        return list(self.modules.keys())
    
    def get_enabled_modules(self) -> List[OrchestratorModule]:
        """Get all enabled modules in priority order"""
        enabled = [m for m in self.modules.values() if m.config.enabled]
        return sorted(enabled, key=lambda m: m.config.priority)
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        Initialize all enabled modules in priority order.
        Returns dict of module_name -> success status.
        """
        results = {}
        for module in self.get_enabled_modules():
            results[module.name] = await module.initialize()
        return results
    
    async def cleanup_all(self):
        """Cleanup all modules in reverse priority order"""
        for module in reversed(self.get_enabled_modules()):
            await module.cleanup()
    
    def _update_initialization_order(self):
        """Update initialization order based on dependencies and priorities"""
        # Simple priority-based ordering for now
        # Could be enhanced with topological sort for complex dependencies
        self._initialization_order = [
            m.name for m in sorted(
                self.modules.values(),
                key=lambda m: m.config.priority
            )
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all modules"""
        return {
            name: module.get_status()
            for name, module in self.modules.items()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from all modules"""
        metrics = {}
        for name, module in self.modules.items():
            module_metrics = module.get_metrics()
            if module_metrics:
                metrics[name] = module_metrics
        return metrics