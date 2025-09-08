"""
Adaptive Parallelism Controller for Self-Improving Orchestrator
"""
import json
import os
import time
from typing import Dict, List, Optional


class AdaptiveParallelism:
    def __init__(self, initial: int = 5, lo: int = 2, hi: int = 64):
        self.cur = initial
        self.lo = lo
        self.hi = hi
        self.history: List[Dict] = []
        self.last_adjustment = time.time()
        self.adjustment_cooldown = 30  # seconds between adjustments

    def update(self, success_rate: float, avg_latency: float, total_tasks: int = 0):
        """Update parallelism based on observed performance"""
        now = time.time()

        # Record metrics
        self.history.append(
            {
                "timestamp": now,
                "parallelism": self.cur,
                "success_rate": success_rate,
                "avg_latency": avg_latency,
                "total_tasks": total_tasks,
            }
        )

        # Keep last 100 entries
        if len(self.history) > 100:
            self.history = self.history[-100:]

        # Adjust with cooldown
        if now - self.last_adjustment < self.adjustment_cooldown:
            return

        old_val = self.cur

        # Increase parallelism if doing well and not hitting limits
        if success_rate > 0.98 and avg_latency < 3.0 and self.cur < self.hi:
            self.cur = min(self.hi, self.cur + 1)
        # Decrease if failing too much or too slow
        elif (success_rate < 0.9 or avg_latency > 10.0) and self.cur > self.lo:
            self.cur = max(self.lo, self.cur - 1)

        if self.cur != old_val:
            self.last_adjustment = now
            self._save_state()

    def value(self) -> int:
        return self.cur

    def get_metrics(self) -> Dict:
        """Get current performance metrics"""
        if not self.history:
            return {"parallelism": self.cur, "data_points": 0}

        recent = self.history[-10:]  # Last 10 data points
        avg_success = sum(h["success_rate"] for h in recent) / len(recent)
        avg_latency = sum(h["avg_latency"] for h in recent) / len(recent)

        return {
            "parallelism": self.cur,
            "recent_success_rate": avg_success,
            "recent_avg_latency": avg_latency,
            "data_points": len(self.history),
            "range": [self.lo, self.hi],
            "last_adjustment": self.last_adjustment,
        }

    def _save_state(self):
        """Save current state for persistence"""
        state_file = os.getenv("ORCH_STATE_FILE", ".adaptive_parallelism.json")
        try:
            with open(state_file, "w") as f:
                json.dump(
                    {
                        "parallelism": self.cur,
                        "history": self.history[-10:],  # Save recent history
                        "last_adjustment": self.last_adjustment,
                    },
                    f,
                    indent=2,
                )
        except Exception:
            pass  # Don't fail if we can't save state

    @classmethod
    def load_state(cls, initial: int = 5, lo: int = 2, hi: int = 64):
        """Load saved state or create new instance"""
        state_file = os.getenv("ORCH_STATE_FILE", ".adaptive_parallelism.json")
        try:
            with open(state_file, "r") as f:
                state = json.load(f)

            instance = cls(initial, lo, hi)
            instance.cur = state.get("parallelism", initial)
            instance.history = state.get("history", [])
            instance.last_adjustment = state.get("last_adjustment", time.time())
            return instance
        except Exception:
            return cls(initial, lo, hi)


class TokenEfficiencyTracker:
    """Track token usage and cost efficiency"""

    def __init__(self):
        self.usage_history: List[Dict] = []

    def record_usage(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        latency: float,
        success: bool,
    ):
        """Record token usage for efficiency analysis"""
        self.usage_history.append(
            {
                "timestamp": time.time(),
                "provider": provider,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "latency": latency,
                "success": success,
                "tokens_per_second": (input_tokens + output_tokens) / max(latency, 0.1),
            }
        )

        # Keep last 1000 entries
        if len(self.usage_history) > 1000:
            self.usage_history = self.usage_history[-1000:]

    def get_provider_efficiency(self, provider: str) -> Dict:
        """Get efficiency metrics for a specific provider"""
        provider_data = [h for h in self.usage_history if h["provider"] == provider]
        if not provider_data:
            return {}

        total_tokens = sum(h["total_tokens"] for h in provider_data)
        avg_latency = sum(h["latency"] for h in provider_data) / len(provider_data)
        success_rate = sum(h["success"] for h in provider_data) / len(provider_data)
        avg_tokens_per_sec = sum(h["tokens_per_second"] for h in provider_data) / len(
            provider_data
        )

        return {
            "provider": provider,
            "total_tokens": total_tokens,
            "avg_latency": avg_latency,
            "success_rate": success_rate,
            "tokens_per_second": avg_tokens_per_sec,
            "sample_count": len(provider_data),
        }

    def recommend_provider(self, context_size: int) -> str:
        """Recommend best provider based on context size and efficiency"""
        providers = list(set(h["provider"] for h in self.usage_history))
        if not providers:
            return "claude"  # Default

        # Simple heuristic: OpenAI for small contexts, Claude for large
        if context_size < 128000:  # 128K tokens
            return "openai" if "openai" in providers else providers[0]
        else:
            return "claude" if "claude" in providers else providers[0]
