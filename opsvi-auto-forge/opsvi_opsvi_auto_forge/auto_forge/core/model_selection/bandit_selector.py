"""Bandit-based model selection using Thompson Sampling."""

import asyncio
import json
import logging
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class ArmStats:
    """Statistics for a bandit arm (model)."""

    alpha: float = 1.0  # Beta distribution alpha parameter
    beta: float = 1.0  # Beta distribution beta parameter
    pulls: int = 0  # Number of times this arm was pulled
    total_reward: float = 0.0  # Cumulative reward
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)

    @property
    def mean_reward(self) -> float:
        """Calculate mean reward."""
        return self.total_reward / max(self.pulls, 1)

    @property
    def expected_value(self) -> float:
        """Calculate expected value using Beta distribution."""
        return self.alpha / (self.alpha + self.beta)

    def update(self, reward: float):
        """Update arm statistics with new reward."""
        self.pulls += 1
        self.total_reward += reward

        # Update Beta distribution parameters
        if reward > 0:
            self.alpha += reward
        else:
            self.beta += abs(reward)

        self.last_updated = datetime.now(timezone.utc)


class BanditModelSelector(BaseModel):
    """Thompson Sampling bandit for model selection."""

    arms: Dict[str, ArmStats] = {}
    exploration_rate: float = 0.1
    min_pulls_for_exploitation: int = 5
    redis_client: Optional[object] = None
    redis_key_prefix: str = "bandit:model:"

    class Config:
        arbitrary_types_allowed = True

    def register_arm(
        self, model_id: str, initial_alpha: float = 1.0, initial_beta: float = 1.0
    ) -> None:
        """Register a new model arm."""
        if model_id not in self.arms:
            self.arms[model_id] = ArmStats(alpha=initial_alpha, beta=initial_beta)
            logger.info(f"Registered new arm: {model_id}")
            asyncio.create_task(self._persist_arm_stats(model_id))

    def select_arm(self) -> str:
        """Select an arm using Thompson Sampling."""
        if not self.arms:
            raise ValueError("No arms registered")

        # Exploration: randomly select an arm with low exploration_rate probability
        if random.random() < self.exploration_rate:
            arm_id = random.choice(list(self.arms.keys()))
            logger.debug(f"Exploration: selected arm {arm_id}")
            return arm_id

        # Exploitation: use Thompson Sampling
        best_arm = None
        best_sample = -1

        for arm_id, stats in self.arms.items():
            # Sample from Beta distribution
            sample = np.random.beta(stats.alpha, stats.beta)

            # Apply exploration bonus for arms with few pulls
            if stats.pulls < self.min_pulls_for_exploitation:
                sample += 0.1  # Small bonus for exploration

            if sample > best_sample:
                best_sample = sample
                best_arm = arm_id

        if best_arm is None:
            # Fallback to random selection
            best_arm = random.choice(list(self.arms.keys()))

        logger.debug(
            f"Thompson Sampling: selected arm {best_arm} (sample: {best_sample:.3f})"
        )
        return best_arm

    async def update_reward(self, model_id: str, reward: float) -> None:
        """Update reward for a model arm."""
        if model_id not in self.arms:
            logger.warning(
                f"Attempted to update reward for unregistered arm: {model_id}"
            )
            return

        # Clamp reward to [0, 1] range
        reward = max(0.0, min(1.0, reward))

        # Update local stats
        self.arms[model_id].update(reward)

        # Persist to Redis
        await self._persist_arm_stats(model_id)

        logger.info(
            f"Updated reward for {model_id}: {reward:.3f} (mean: {self.arms[model_id].mean_reward:.3f})"
        )

    async def get_arm_stats(self, model_id: str) -> Optional[ArmStats]:
        """Get statistics for a specific arm."""
        return self.arms.get(model_id)

    async def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all arms."""
        return {
            arm_id: {
                "alpha": stats.alpha,
                "beta": stats.beta,
                "pulls": stats.pulls,
                "total_reward": stats.total_reward,
                "mean_reward": stats.mean_reward,
                "expected_value": stats.expected_value,
                "last_updated": stats.last_updated.isoformat(),
            }
            for arm_id, stats in self.arms.items()
        }

    async def load_from_redis(self) -> None:
        """Load arm statistics from Redis."""
        if not self.redis_client:
            logger.warning("Redis client not available, skipping load")
            return

        try:
            for arm_id in self.arms.keys():
                redis_key = f"{self.redis_key_prefix}{arm_id}"
                data = await self.redis_client.get(redis_key)

                if data:
                    stats_data = json.loads(data)
                    stats = ArmStats(
                        alpha=stats_data.get("alpha", 1.0),
                        beta=stats_data.get("beta", 1.0),
                        pulls=stats_data.get("pulls", 0),
                        total_reward=stats_data.get("total_reward", 0.0),
                        last_updated=datetime.fromisoformat(
                            stats_data.get(
                                "last_updated", datetime.now(timezone.utc).isoformat()
                            )
                        ),
                    )
                    self.arms[arm_id] = stats
                    logger.info(f"Loaded stats for arm {arm_id} from Redis")

        except Exception as e:
            logger.error(f"Failed to load arm stats from Redis: {e}")

    async def _persist_arm_stats(self, model_id: str) -> None:
        """Persist arm statistics to Redis."""
        if not self.redis_client:
            return

        try:
            stats = self.arms[model_id]
            redis_key = f"{self.redis_key_prefix}{model_id}"

            data = {
                "alpha": stats.alpha,
                "beta": stats.beta,
                "pulls": stats.pulls,
                "total_reward": stats.total_reward,
                "last_updated": stats.last_updated.isoformat(),
            }

            await self.redis_client.set(
                redis_key, json.dumps(data), ex=86400
            )  # 24 hour expiry

        except Exception as e:
            logger.error(f"Failed to persist arm stats to Redis: {e}")

    def reset_arm(self, model_id: str) -> None:
        """Reset statistics for an arm."""
        if model_id in self.arms:
            self.arms[model_id] = ArmStats()
            logger.info(f"Reset stats for arm {model_id}")

    def get_best_arm(self) -> Optional[str]:
        """Get the arm with the highest expected value."""
        if not self.arms:
            return None

        best_arm = max(self.arms.items(), key=lambda x: x[1].expected_value)
        return best_arm[0]


# Global bandit selector instance
_bandit_selector: Optional[BanditModelSelector] = None


def get_bandit_selector(redis_client: Optional[object] = None) -> BanditModelSelector:
    """Get or create the global bandit selector instance."""
    global _bandit_selector

    if _bandit_selector is None:
        _bandit_selector = BanditModelSelector(redis_client=redis_client)
        logger.info("Created new bandit selector instance")

    return _bandit_selector


async def select_model_bandit(
    available_models: List[str], redis_client: Optional[object] = None
) -> str:
    """Select a model using bandit algorithm."""
    selector = get_bandit_selector(redis_client)

    # Register any new models
    for model_id in available_models:
        if model_id not in selector.arms:
            selector.register_arm(model_id)

    # Load stats from Redis if available
    if redis_client:
        await selector.load_from_redis()

    # Select arm
    selected_model = selector.select_arm()

    # Ensure the selected model is in available models
    if selected_model not in available_models:
        logger.warning(
            f"Selected model {selected_model} not in available models, using first available"
        )
        selected_model = available_models[0]

    return selected_model


async def update_model_reward(
    model_id: str, reward: float, redis_client: Optional[object] = None
) -> None:
    """Update reward for a model."""
    selector = get_bandit_selector(redis_client)
    await selector.update_reward(model_id, reward)
