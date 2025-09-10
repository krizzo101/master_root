"""
OpenAI Provider for Multi-Provider Orchestrator
Handles OpenAI API integration with token management
"""
import os
import time
from typing import Any, Dict

from openai import OpenAI


class OpenAIProvider:
    def __init__(self, api_key: str = None, daily_limits: Dict = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

        # Daily token limits
        self.limits = daily_limits or {
            "premium": 1000000,  # o4-mini
            "standard": 10000000,  # gpt-5, gpt-5-mini
        }

        # Track usage
        self.usage = {"premium": 0, "standard": 0}
        self.last_reset = time.time()

        # Model mapping
        self.models = {
            "premium": "o4-mini",
            "standard": "gpt-5-mini",
            "fallback": "gpt-5",
        }

    def has_capacity(self) -> bool:
        """Check if provider has available tokens"""
        self._reset_daily_limits()
        return (
            self.usage["premium"] < self.limits["premium"]
            or self.usage["standard"] < self.limits["standard"]
        )

    def get_available_capacity(self) -> Dict[str, int]:
        """Get remaining token capacity"""
        self._reset_daily_limits()
        return {
            "premium": max(0, self.limits["premium"] - self.usage["premium"]),
            "standard": max(0, self.limits["standard"] - self.usage["standard"]),
        }

    def select_model(self, task_complexity: str = "medium") -> str:
        """Select optimal model based on task complexity"""
        capacity = self.get_available_capacity()

        if task_complexity in ["simple", "low"] and capacity["premium"] > 1000:
            return self.models["premium"]
        elif capacity["standard"] > 5000:
            return self.models["standard"]
        elif capacity["standard"] > 1000:
            return self.models["fallback"]
        else:
            return None  # No capacity

    def execute_task(self, task: Any, model: str = None) -> Dict:
        """Execute task using OpenAI API"""
        if not self.client:
            raise ValueError("OpenAI API key not configured")

        model = model or self.select_model()
        if not model:
            raise ValueError("No OpenAI capacity available")

        try:
            # Estimate tokens for tracking
            estimated_tokens = self._estimate_tokens(task.prompt)

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": task.prompt},
                ],
                max_tokens=4000,
                temperature=0.1,
            )

            # Track usage
            tier = "premium" if model == self.models["premium"] else "standard"
            self.usage[tier] += estimated_tokens

            return {
                "status": "completed",
                "result": response.choices[0].message.content,
                "model_used": model,
                "tokens_used": estimated_tokens,
                "provider": "openai",
            }

        except Exception as e:
            return {"status": "failed", "error": str(e), "provider": "openai"}

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token)"""
        return len(text) // 4

    def _reset_daily_limits(self):
        """Reset usage counters at midnight"""
        now = time.time()
        if now - self.last_reset > 86400:  # 24 hours
            self.usage = {"premium": 0, "standard": 0}
            self.last_reset = now

    def get_status(self) -> Dict:
        """Get provider status"""
        capacity = self.get_available_capacity()
        return {
            "provider": "openai",
            "available": self.has_capacity(),
            "capacity": capacity,
            "models": self.models,
            "usage": self.usage,
        }
