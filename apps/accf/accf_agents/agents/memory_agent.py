"""
Memory Agent - Refactored version for the new ACCF agents structure.

This module provides a refactored version of the original memory_agent.py,
focused on memory management and retrieval operations.
"""

import time
from typing import Dict, Any, List
from .base import BaseAgent, Task, Result


class MemoryAgent(BaseAgent):
    """
    Memory Agent for managing and retrieving persistent memory.

    Handles memory operations including storage, retrieval, and LLM-backed Q&A
    using stored memory context.
    """

    def __init__(self, name: str, settings: Any):
        super().__init__(name, settings)
        self.memory: Dict[str, Any] = {}
        self.logger.info("=== MEMORY AGENT INITIALIZED ===")

    def can_handle(self, task_type: str) -> bool:
        """Check if this agent can handle the given task type."""
        return task_type in [
            "memory_store",
            "memory_retrieve",
            "memory_answer",
            "memory_clear",
            "memory_list",
        ]

    def get_capabilities(self) -> List[str]:
        """Get list of task types this agent can handle."""
        return [
            "memory_store",
            "memory_retrieve",
            "memory_answer",
            "memory_clear",
            "memory_list",
        ]

    async def execute(self, task: Task) -> Result:
        """Execute a memory task."""
        try:
            self.logger.info(f"Executing memory task: {task.id}")

            task_type = task.type
            parameters = task.parameters

            if task_type == "memory_store":
                response = await self._store_memory(parameters)
            elif task_type == "memory_retrieve":
                response = await self._retrieve_memory(parameters)
            elif task_type == "memory_answer":
                response = await self._answer_with_memory(parameters)
            elif task_type == "memory_clear":
                response = await self._clear_memory(parameters)
            elif task_type == "memory_list":
                response = await self._list_memory(parameters)
            else:
                raise ValueError(f"Unknown memory task type: {task_type}")

            return Result(
                task_id=task.id,
                status="success",
                data=response,
                execution_time=time.time(),
            )

        except Exception as e:
            self.logger.error(f"Error executing memory task {task.id}: {e}")
            return Result(
                task_id=task.id,
                status="error",
                data={},
                error_message=str(e),
                execution_time=time.time(),
            )

    async def _store_memory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Store a value in persistent memory."""
        key = parameters.get("key", "")
        value = parameters.get("value")

        if not key:
            raise ValueError("Memory key is required")

        self.memory[key] = value
        self.logger.info(f"Stored memory key={key}")

        return {
            "key": key,
            "stored": True,
            "timestamp": time.time(),
        }

    async def _retrieve_memory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve a value from persistent memory."""
        key = parameters.get("key", "")

        if not key:
            raise ValueError("Memory key is required")

        value = self.memory.get(key)
        self.logger.info(f"Retrieved memory key={key}")

        return {
            "key": key,
            "value": value,
            "found": key in self.memory,
            "timestamp": time.time(),
        }

    async def _answer_with_memory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Answer a question using LLM and stored memory context."""
        prompt = parameters.get("prompt", "")

        if not prompt:
            raise ValueError("Prompt is required for memory answer")

        try:
            # Build context from stored memory
            context = "\n".join(f"{k}: {v}" for k, v in self.memory.items())
            full_prompt = f"Memory Context:\n{context}\n\nQuestion: {prompt}"

            self.logger.debug(f"Memory answer prompt: {full_prompt}")

            # Placeholder for LLM integration
            # In the full implementation, this would use the OpenAI interface
            response = {
                "answer": f"Based on memory context: {prompt}",
                "context": context,
                "memory_keys_used": list(self.memory.keys()),
                "timestamp": time.time(),
            }

            return response

        except Exception as e:
            self.logger.error(f"Memory answer failed: {e}")
            return {
                "answer": f"[Error: {e}]",
                "context": "",
                "error": str(e),
                "timestamp": time.time(),
            }

    async def _clear_memory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clear memory - either specific key or all memory."""
        key = parameters.get("key")

        if key:
            # Clear specific key
            if key in self.memory:
                del self.memory[key]
                self.logger.info(f"Cleared memory key: {key}")
                return {
                    "cleared_key": key,
                    "cleared": True,
                    "timestamp": time.time(),
                }
            else:
                return {
                    "cleared_key": key,
                    "cleared": False,
                    "error": "Key not found",
                    "timestamp": time.time(),
                }
        else:
            # Clear all memory
            count = len(self.memory)
            self.memory.clear()
            self.logger.info(f"Cleared all memory ({count} items)")
            return {
                "cleared_all": True,
                "items_cleared": count,
                "timestamp": time.time(),
            }

    async def _list_memory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List all memory keys and optionally their values."""
        include_values = parameters.get("include_values", False)

        if include_values:
            return {
                "memory": self.memory.copy(),
                "total_items": len(self.memory),
                "timestamp": time.time(),
            }
        else:
            return {
                "keys": list(self.memory.keys()),
                "total_items": len(self.memory),
                "timestamp": time.time(),
            }
