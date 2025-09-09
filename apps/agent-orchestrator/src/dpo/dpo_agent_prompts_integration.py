#!/usr/bin/env python3
"""
DPO Agent Prompts Integration

Integrates DPO enhancement levels with agent system prompts to automatically
provide specialized instructions to agents based on the enhancement dial setting.
"""

import sys
from pathlib import Path
from typing import List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent_system_prompts import get_prompt_manager
from src.dpo.enhancement_config import DPOEnhancementConfig
from src.generic_orchestrator import AgentTask


class DPOAgentPromptsIntegration:
    """Integrates DPO enhancement with agent system prompts"""

    def __init__(self, dpo_config: Optional[DPOEnhancementConfig] = None):
        """
        Initialize the integration.

        Args:
            dpo_config: DPO enhancement configuration
        """
        self.dpo_config = dpo_config or DPOEnhancementConfig()
        self.prompt_manager = get_prompt_manager()

    def enhance_tasks_with_prompts(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """
        Enhance tasks with appropriate system prompts based on DPO level.

        Args:
            tasks: List of agent tasks to enhance

        Returns:
            Enhanced tasks with system prompts configured
        """
        if not self.dpo_config.enabled:
            return tasks

        enhancement_level = self.dpo_config.level.to_number()

        for task in tasks:
            # Skip if task already has custom prompt configuration
            if hasattr(task, "system_prompt") and task.system_prompt:
                continue

            # Set enhancement level
            task.enhancement_level = enhancement_level

            # Add level-specific enhancements
            if enhancement_level >= 3:
                # Balanced and above: Add detailed instructions
                task.system_prompt = self._get_enhanced_instructions(
                    task.task_type, enhancement_level
                )

            if enhancement_level >= 4:
                # Comprehensive: Add quality focus
                if not task.system_prompt:
                    task.system_prompt = ""
                task.system_prompt += " Focus on production quality, comprehensive testing, and detailed documentation."

            if enhancement_level >= 5:
                # Maximum: Add innovation focus
                if not task.system_prompt:
                    task.system_prompt = ""
                task.system_prompt += " Consider innovative approaches and emerging best practices. Provide multiple solution options with detailed trade-off analysis."

        return tasks

    def _get_enhanced_instructions(self, task_type: str, level: int) -> str:
        """Get enhanced instructions for a task type"""
        instructions = []

        # Get agent traits
        traits = self.prompt_manager.get_agent_traits(task_type)
        if traits:
            instructions.append(f"Apply these key traits: {', '.join(traits)}.")

        # Get tool focus
        tools = self.prompt_manager.get_tool_focus(task_type)
        if tools and level >= 3:
            instructions.append(
                f"Focus on using these tools effectively: {', '.join(tools)}."
            )

        # Add level-specific guidance
        if level >= 3:
            instructions.append("Be thorough and systematic in your approach.")
        if level >= 4:
            instructions.append("Consider edge cases and failure scenarios.")
        if level >= 5:
            instructions.append(
                "Apply cutting-edge best practices and innovative solutions."
            )

        return " ".join(instructions) if instructions else ""

    def get_recommended_agent_for_task(self, task_description: str) -> str:
        """
        Recommend the best agent type for a task description.

        Args:
            task_description: Description of the task

        Returns:
            Recommended agent type
        """
        # Keywords mapping to agent types
        keyword_mapping = {
            "requirements": "requirements-analyst",
            "business": "business-analyst",
            "architecture": "solution-architect",
            "database": "database-specialist",
            "develop": "development-specialist",
            "implement": "development-specialist",
            "api": "api-integration-specialist",
            "test": "qa-testing-guru",
            "security": "security-architect",
            "deploy": "devops-automation",
            "ci/cd": "devops-automation",
            "performance": "performance-optimizer",
            "document": "technical-writer",
            "research": "research-specialist",
            "monitor": "monitoring-specialist",
        }

        task_lower = task_description.lower()
        for keyword, agent_type in keyword_mapping.items():
            if keyword in task_lower:
                return agent_type

        return "development-specialist"  # Default

    def create_enhanced_task(
        self, task_id: str, prompt: str, dependencies: List[str] = None
    ) -> AgentTask:
        """
        Create an enhanced task with automatic agent selection and prompts.

        Args:
            task_id: Task identifier
            prompt: Task prompt
            dependencies: Task dependencies

        Returns:
            Enhanced AgentTask
        """
        # Determine agent type
        agent_type = self.get_recommended_agent_for_task(prompt)

        # Create task
        task = AgentTask(
            task_id=task_id,
            task_type=agent_type,
            prompt=prompt,
            dependencies=dependencies or [],
            enhancement_level=self.dpo_config.level.to_number(),
        )

        # Enhance with prompts
        enhanced_tasks = self.enhance_tasks_with_prompts([task])
        return enhanced_tasks[0]

    def get_enhancement_summary(self) -> dict:
        """Get a summary of current enhancement settings"""
        return {
            "enabled": self.dpo_config.enabled,
            "level": self.dpo_config.level.value,
            "level_number": self.dpo_config.level.to_number(),
            "max_agents": self.dpo_config.max_agents,
            "max_tasks_per_phase": self.dpo_config.max_tasks_per_phase,
            "features": {
                "quality_gates": self.dpo_config.add_quality_gates,
                "documentation": self.dpo_config.add_documentation,
                "testing": self.dpo_config.add_testing,
                "best_practices": self.dpo_config.add_best_practices,
                "infer_requirements": self.dpo_config.infer_requirements,
            },
            "available_agents": self.prompt_manager.list_available_agents(),
        }
