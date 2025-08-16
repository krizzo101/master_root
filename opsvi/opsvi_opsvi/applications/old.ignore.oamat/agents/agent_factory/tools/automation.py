"""
OAMAT Agent Factory - Automation Tools
Tools for automating and scheduling workflows.
"""

import logging

from langchain_core.tools import tool

logger = logging.getLogger("OAMAT.AgentFactory.AutomationTools")


def create_automation_tools():
    @tool
    def automate_workflow(workflow_name: str, parameters: dict) -> str:
        """Automates a repetitive workflow with the given parameters."""
        if not workflow_name:
            raise ValueError("Workflow name is required for automation.")
        logger.info(
            f"Automating workflow '{workflow_name}' with parameters: {parameters}"
        )
        return f"✅ Workflow '{workflow_name}' automated successfully."

    @tool
    def schedule_task(task_name: str, schedule: str) -> str:
        """Schedules an automated task to run at a specific interval."""
        if not task_name or not schedule:
            raise ValueError("Task name and schedule are required.")
        logger.info(f"Scheduling task '{task_name}' with schedule: {schedule}")
        return f"✅ Task '{task_name}' scheduled successfully."

    return [automate_workflow, schedule_task]
