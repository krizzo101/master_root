"""
Hybrid AI controller combining Claude CLI and OpenAI API.
Updated for async compatibility and STRICT 2025 model compliance.
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.config import TetraConfig
from .model_config import ModelConfig
from .openai_adapter import OpenAIAdapter

logger = logging.getLogger(__name__)


class HybridController:
    """Manages hybrid AI operations with STRICT model compliance."""

    def __init__(self, config: Optional[TetraConfig] = None):
        """Initialize hybrid controller with STRICT validation."""
        self.config = config or TetraConfig()
        self.model_config = ModelConfig()
        self.openai_adapter = OpenAIAdapter(self.model_config)
        self.claude_bin = self.config.ai.claude_bin

    async def route_task(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route task to appropriate AI provider based on task type.

        Args:
            task: Task description
            context: Optional context

        Returns:
            Task result with metadata
        """
        # Analyze task type using OpenAI with STRICT compliance
        analysis = await self.openai_adapter.analyze_task(task, context)

        if analysis["task_type"] == "code_generation":
            return await self._execute_claude(task, context)
        elif analysis["task_type"] in ["reasoning", "planning"]:
            return await self._execute_openai_reasoning(task, context)
        else:
            return await self._execute_openai_general(task, context)

    async def _execute_claude(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute task using Claude CLI."""
        try:
            cmd = [
                str(self.claude_bin),
                "code",
                "--model",
                self.config.ai.claude_model,
                "--permission-mode",
                self.config.ai.claude_permission_mode,
                "--allowed-tools",
                self.config.ai.claude_allowed_tools,
                "--max-turns",
                str(self.config.ai.claude_max_turns),
            ]

            # Add context if provided
            if context and context.get("files"):
                for file in context["files"]:
                    cmd.extend(["--file", str(file)])

            # Add the task
            cmd.append(task)

            # Run Claude
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=self.config.ai.claude_timeout,
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                raise RuntimeError(f"Claude execution failed: {stderr.decode()}")

            return {
                "provider": "claude",
                "model": self.config.ai.claude_model,
                "result": stdout.decode(),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Claude execution failed: {e}")
            return {"provider": "claude", "error": str(e), "success": False}

    async def _execute_openai_reasoning(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute reasoning task using OpenAI with STRICT compliance."""
        try:
            model = self.model_config.get_model_for_task("reasoning")
            result = await self.openai_adapter.execute_reasoning(task, context, model)

            return {"provider": "openai", "model": model, "result": result, "success": True}

        except Exception as e:
            logger.error(f"OpenAI reasoning failed: {e}")
            return {"provider": "openai", "error": str(e), "success": False}

    async def _execute_openai_general(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute general task using OpenAI with STRICT compliance."""
        try:
            model = self.model_config.get_model_for_task("execution")
            result = await self.openai_adapter.execute_task(task, context, model)

            return {"provider": "openai", "model": model, "result": result, "success": True}

        except Exception as e:
            logger.error(f"OpenAI execution failed: {e}")
            return {"provider": "openai", "error": str(e), "success": False}

    async def batch_process(self, tasks: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple tasks in parallel with STRICT compliance.

        Args:
            tasks: List of task descriptions

        Returns:
            List of results
        """
        # Create async tasks
        async_tasks = [self.route_task(task) for task in tasks]

        # Execute in parallel
        results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({"task": tasks[i], "error": str(result), "success": False})
            else:
                result["task"] = tasks[i]
                processed_results.append(result)

        return processed_results

    def validate_models(self) -> Dict[str, Any]:
        """Validate all configured models against STRICT standards."""
        validation_results = {"config_valid": True, "models": {}, "errors": []}

        # Validate reasoning model
        try:
            reasoning_model = self.model_config.get_model_for_task("reasoning")
            validation_results["models"]["reasoning"] = {"model": reasoning_model, "valid": True}
        except Exception as e:
            validation_results["config_valid"] = False
            validation_results["errors"].append(f"Reasoning model error: {e}")

        # Validate execution model
        try:
            execution_model = self.model_config.get_model_for_task("execution")
            validation_results["models"]["execution"] = {"model": execution_model, "valid": True}
        except Exception as e:
            validation_results["config_valid"] = False
            validation_results["errors"].append(f"Execution model error: {e}")

        # Validate Claude configuration
        if not self.claude_bin.exists():
            validation_results["errors"].append(f"Claude binary not found: {self.claude_bin}")

        return validation_results
