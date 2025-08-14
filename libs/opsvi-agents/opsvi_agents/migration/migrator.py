"""Agent migration utilities."""

from typing import Any, Dict, List, Optional, Type
from pathlib import Path
import json
import importlib.util

import structlog

from ..core import BaseAgent, AgentConfig
from ..adapters import UniversalAgentAdapter
from ..registry import registry as agent_registry

logger = structlog.get_logger(__name__)


class AgentMigrator:
    """Migrate legacy agents to V2 framework."""
    
    def __init__(self):
        """Initialize migrator."""
        self._logger = logger.bind(component="AgentMigrator")
        self.migration_report: List[Dict[str, Any]] = []
    
    def migrate_from_module(
        self,
        module_path: str,
        agent_class_name: str,
        new_name: str = None
    ) -> BaseAgent:
        """Migrate agent from Python module."""
        try:
            # Load module
            spec = importlib.util.spec_from_file_location("legacy_module", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get agent class
            agent_class = getattr(module, agent_class_name)
            
            # Create V2 config
            config = AgentConfig(
                name=new_name or agent_class_name.lower(),
                metadata={"migrated_from": module_path}
            )
            
            # Create adapter
            adapter = UniversalAgentAdapter.from_legacy_class(agent_class, config)
            
            # Register in V2 registry
            agent_registry.register(
                name=config.name,
                agent_class=UniversalAgentAdapter,
                description=f"Migrated from {agent_class_name}",
                default_config=config,
                tags=["migrated", "legacy"]
            )
            
            self._logger.info(f"Migrated agent: {agent_class_name} -> {config.name}")
            
            self.migration_report.append({
                "source": module_path,
                "class": agent_class_name,
                "target": config.name,
                "status": "success"
            })
            
            return adapter
            
        except Exception as e:
            self._logger.error(f"Migration failed: {e}")
            self.migration_report.append({
                "source": module_path,
                "class": agent_class_name,
                "status": "failed",
                "error": str(e)
            })
            raise
    
    def migrate_from_config(
        self,
        config_path: str,
        adapter_class: Type[BaseAgent] = UniversalAgentAdapter
    ) -> List[BaseAgent]:
        """Migrate agents from configuration file."""
        agents = []
        
        with open(config_path, "r") as f:
            configs = json.load(f)
        
        for config_data in configs:
            try:
                # Create V2 config
                config = AgentConfig(
                    name=config_data.get("name", "unnamed_agent"),
                    model=config_data.get("model", "gpt-4o-mini"),
                    temperature=config_data.get("temperature", 0.7),
                    metadata=config_data.get("metadata", {})
                )
                
                # Create adapter
                adapter = adapter_class(config)
                
                # Register
                agent_registry.register(
                    name=config.name,
                    agent_class=adapter_class,
                    default_config=config,
                    tags=["migrated", "config"]
                )
                
                agents.append(adapter)
                
                self.migration_report.append({
                    "source": config_path,
                    "name": config.name,
                    "status": "success"
                })
                
            except Exception as e:
                self._logger.error(f"Failed to migrate {config_data}: {e}")
                self.migration_report.append({
                    "source": config_path,
                    "name": config_data.get("name", "unknown"),
                    "status": "failed",
                    "error": str(e)
                })
        
        self._logger.info(f"Migrated {len(agents)} agents from {config_path}")
        return agents
    
    def migrate_directory(
        self,
        directory: str,
        pattern: str = "*.py"
    ) -> List[BaseAgent]:
        """Migrate all agents from directory."""
        agents = []
        dir_path = Path(directory)
        
        for file_path in dir_path.glob(pattern):
            if file_path.name.startswith("_"):
                continue
            
            try:
                # Attempt to find agent classes in file
                spec = importlib.util.spec_from_file_location(
                    file_path.stem,
                    file_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find agent classes
                for name, obj in vars(module).items():
                    if (isinstance(obj, type) and 
                        name.endswith("Agent") and
                        not name.startswith("_")):
                        
                        agent = self.migrate_from_module(
                            str(file_path),
                            name,
                            f"{file_path.stem}_{name.lower()}"
                        )
                        agents.append(agent)
                        
            except Exception as e:
                self._logger.error(f"Failed to process {file_path}: {e}")
        
        return agents
    
    def generate_report(self, output_path: str = None) -> Dict[str, Any]:
        """Generate migration report."""
        successful = [r for r in self.migration_report if r["status"] == "success"]
        failed = [r for r in self.migration_report if r["status"] == "failed"]
        
        report = {
            "total": len(self.migration_report),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.migration_report) if self.migration_report else 0,
            "details": self.migration_report
        }
        
        if output_path:
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
            self._logger.info(f"Report saved to {output_path}")
        
        return report
    
    def validate_migration(self, agent: BaseAgent, test_prompt: str = "Hello") -> bool:
        """Validate migrated agent works."""
        try:
            result = agent.execute(test_prompt)
            return result.success
        except Exception as e:
            self._logger.error(f"Validation failed: {e}")
            return False


# Global migrator instance
migrator = AgentMigrator()
