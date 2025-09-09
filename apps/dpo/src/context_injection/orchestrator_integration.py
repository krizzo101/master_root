#!/usr/bin/env python3
"""
Orchestrator Integration for Context Injection System
Seamlessly integrates context injection with the generic orchestrator
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .context_system import ContextInjectionSystem, get_context_system

logger = logging.getLogger(__name__)


class OrchestratorContextInjector:
    """Integrates context injection with the orchestrator's agent task system"""

    def __init__(self, master_root: str = "/home/opsvi/master_root"):
        self.context_system = get_context_system(master_root)
        self.task_type_to_agent_type = {
            "documentation": "documentation",
            "development": "development",
            "integration": "integration",
            "monitoring": "monitoring",
            "analysis": "analysis",
            "orchestration": "orchestration",
            "system-documentation": "documentation",
            "api-development": "development",
            "test-creation": "development",
            "performance-analysis": "analysis",
            "system-integration": "integration",
        }

    def enhance_agent_task(self, task: "AgentTask") -> "AgentTask":
        """Enhance an AgentTask with ecosystem context"""

        # Determine agent type from task
        agent_type = self._determine_agent_type(task)

        # Get task description
        task_description = task.context.get("description", task.prompt[:100])

        # Generate enhanced prompt with context
        enhanced_prompt = self.context_system.inject_context(
            agent_type=agent_type,
            task_description=task_description,
            base_prompt=task.prompt,
            additional_context=task.context,
        )

        # Update task with enhanced prompt
        task.prompt = enhanced_prompt

        # Add context reference to task context
        task.context["context_injected"] = True
        task.context["agent_type"] = agent_type
        task.context["ecosystem_context"] = "injected"

        logger.debug(f"Enhanced task {task.task_id} with {agent_type} context")

        return task

    def generate_context_file_for_task(self, task: "AgentTask", output_dir: str) -> str:
        """Generate a context reference file for an agent task"""

        agent_type = self._determine_agent_type(task)
        task_description = task.context.get("description", task.prompt[:100])

        # Generate context file
        context_file_path = Path(output_dir) / f"context_{task.task_id}.json"

        self.context_system.get_context_file(
            agent_type=agent_type,
            task_description=task_description,
            output_path=str(context_file_path),
        )

        return str(context_file_path)

    def _determine_agent_type(self, task: "AgentTask") -> str:
        """Determine agent type from task"""

        # Check explicit agent type in context
        if "agent_type" in task.context:
            return task.context["agent_type"]

        # Check task type mapping
        task_type = task.task_type.lower()
        if task_type in self.task_type_to_agent_type:
            return self.task_type_to_agent_type[task_type]

        # Analyze prompt for keywords
        prompt_lower = task.prompt.lower()

        if any(kw in prompt_lower for kw in ["document", "readme", "guide", "manual"]):
            return "documentation"
        elif any(
            kw in prompt_lower for kw in ["develop", "implement", "code", "build"]
        ):
            return "development"
        elif any(
            kw in prompt_lower for kw in ["integrate", "connect", "api", "interface"]
        ):
            return "integration"
        elif any(
            kw in prompt_lower for kw in ["monitor", "metric", "dashboard", "log"]
        ):
            return "monitoring"
        elif any(kw in prompt_lower for kw in ["analyze", "review", "audit", "assess"]):
            return "analysis"

        # Default to general orchestration
        return "orchestration"


def inject_context_into_orchestrator(orchestrator_instance):
    """Monkey-patch an orchestrator instance to add context injection"""

    injector = OrchestratorContextInjector()

    # Store original execute_task method
    original_execute = orchestrator_instance.execute_task

    # Create wrapped version with context injection
    async def execute_with_context(task, agent_index=0):
        # Enhance task with context
        enhanced_task = injector.enhance_agent_task(task)

        # Call original execution
        return await original_execute(enhanced_task, agent_index)

    # Replace method
    orchestrator_instance.execute_task = execute_with_context

    logger.info("Context injection integrated with orchestrator")

    return orchestrator_instance


class ContextAwareOrchestrator:
    """
    Wrapper class that adds context injection to any orchestrator
    """

    def __init__(self, orchestrator_class, *args, **kwargs):
        """
        Initialize with an orchestrator class and its arguments

        Args:
            orchestrator_class: The orchestrator class to wrap
            *args, **kwargs: Arguments to pass to orchestrator initialization
        """
        # Initialize the base orchestrator
        self.orchestrator = orchestrator_class(*args, **kwargs)

        # Initialize context injector
        master_root = kwargs.get("master_root", "/home/opsvi/master_root")
        self.injector = OrchestratorContextInjector(master_root)

        # Wrap key methods
        self._wrap_methods()

    def _wrap_methods(self):
        """Wrap orchestrator methods to add context injection"""

        # Wrap execute_task if it exists
        if hasattr(self.orchestrator, "execute_task"):
            original_execute = self.orchestrator.execute_task

            async def execute_with_context(task, *args, **kwargs):
                # Enhance task with context
                enhanced_task = self.injector.enhance_agent_task(task)
                # Call original
                return await original_execute(enhanced_task, *args, **kwargs)

            self.orchestrator.execute_task = execute_with_context

        # Wrap run method if it exists
        if hasattr(self.orchestrator, "run"):
            original_run = self.orchestrator.run

            async def run_with_context(tasks, *args, **kwargs):
                # Enhance all tasks
                enhanced_tasks = [
                    self.injector.enhance_agent_task(task) for task in tasks
                ]
                # Call original
                return await original_run(enhanced_tasks, *args, **kwargs)

            self.orchestrator.run = run_with_context

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped orchestrator"""
        return getattr(self.orchestrator, name)


def create_context_aware_orchestrator(orchestrator_class, *args, **kwargs):
    """
    Factory function to create a context-aware orchestrator

    Usage:
        from generic_orchestrator import GenericOrchestrator
        from context_injection.orchestrator_integration import create_context_aware_orchestrator

        # Create context-aware orchestrator
        orchestrator = create_context_aware_orchestrator(
            GenericOrchestrator,
            output_dir="outputs/my_task",
            max_parallel_agents=10
        )

        # Use normally - context will be automatically injected
        results = await orchestrator.run(tasks)
    """
    return ContextAwareOrchestrator(orchestrator_class, *args, **kwargs)
