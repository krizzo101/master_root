#!/usr/bin/env python3
"""
Shared Token Pool Manager
Prevents single orchestrator from hoarding all tokens
Uses file-based locking to coordinate between multiple processes
"""

import fcntl
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Set

logger = logging.getLogger(__name__)


class SharedTokenPool:
    """
    Manages token allocation across multiple orchestrator instances
    Ensures fair distribution and prevents token hoarding
    """

    def __init__(
        self,
        max_tokens_per_instance: int = 5,
        token_timeout: int = 600,  # 10 minutes
        lock_dir: Path = Path("/tmp/token_locks"),
    ):
        """
        Args:
            max_tokens_per_instance: Maximum tokens one orchestrator can use
            token_timeout: Seconds before a token is considered abandoned
            lock_dir: Directory for lock files
        """
        self.max_tokens_per_instance = max_tokens_per_instance
        self.token_timeout = token_timeout
        self.lock_dir = lock_dir
        self.lock_dir.mkdir(parents=True, exist_ok=True)

        # Lock file for coordinating access
        self.pool_lock_file = self.lock_dir / "token_pool.lock"
        self.allocation_file = self.lock_dir / "token_allocations.json"

        # Instance ID (process ID + timestamp)
        self.instance_id = f"{os.getpid()}_{int(time.time())}"

        # Load all available tokens
        self._load_all_tokens()

    def _load_all_tokens(self):
        """Load all tokens from encrypted storage"""
        try:
            import sys

            sys.path.insert(0, "/home/opsvi/master_root/apps/multi-agent-monitor")
            from src.orchestration.secrets_manager import TokenSecretsManager

            manager = TokenSecretsManager()
            tokens = manager.load_tokens()

            # Get all token values
            self.all_tokens = []
            for key in sorted(tokens.keys()):
                if key.startswith("CLAUDE_CODE_TOKEN"):
                    self.all_tokens.append(tokens[key])

            logger.info(f"Loaded {len(self.all_tokens)} total tokens")
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            self.all_tokens = []

    def acquire_tokens(self, requested: int = None) -> List[str]:
        """
        Acquire tokens for this instance

        Args:
            requested: Number of tokens requested (capped at max_per_instance)

        Returns:
            List of allocated token strings
        """
        if not self.all_tokens:
            logger.error("No tokens available in pool")
            return []

        # Cap requested tokens at maximum allowed
        if requested is None:
            requested = self.max_tokens_per_instance
        requested = min(requested, self.max_tokens_per_instance)

        allocated_tokens = []

        # Acquire lock for allocation file
        with open(self.pool_lock_file, "w") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)

            try:
                # Load current allocations
                allocations = self._load_allocations()

                # Clean up expired allocations
                allocations = self._cleanup_expired(allocations)

                # Find available tokens
                used_indices = set()
                for instance, data in allocations.items():
                    used_indices.update(data["token_indices"])

                # Allocate tokens to this instance
                my_indices = []
                for i, token in enumerate(self.all_tokens):
                    if i not in used_indices and len(my_indices) < requested:
                        my_indices.append(i)
                        allocated_tokens.append(token)

                if my_indices:
                    # Record allocation
                    allocations[self.instance_id] = {
                        "token_indices": my_indices,
                        "timestamp": datetime.now().isoformat(),
                        "pid": os.getpid(),
                    }

                    # Save allocations
                    self._save_allocations(allocations)

                    logger.info(
                        f"Instance {self.instance_id} acquired {len(my_indices)} tokens: {my_indices}"
                    )
                else:
                    logger.warning(
                        f"No tokens available for instance {self.instance_id}"
                    )

            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

        return allocated_tokens

    def release_tokens(self):
        """Release tokens held by this instance"""
        with open(self.pool_lock_file, "w") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)

            try:
                allocations = self._load_allocations()

                if self.instance_id in allocations:
                    released = allocations[self.instance_id]["token_indices"]
                    del allocations[self.instance_id]
                    self._save_allocations(allocations)
                    logger.info(
                        f"Instance {self.instance_id} released tokens: {released}"
                    )

            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    def get_status(self) -> dict:
        """Get current allocation status"""
        allocations = self._load_allocations()
        allocations = self._cleanup_expired(allocations)

        total_used = sum(len(data["token_indices"]) for data in allocations.values())

        return {
            "total_tokens": len(self.all_tokens),
            "used_tokens": total_used,
            "available_tokens": len(self.all_tokens) - total_used,
            "max_per_instance": self.max_tokens_per_instance,
            "active_instances": len(allocations),
            "instance_details": {
                instance: {
                    "tokens": len(data["token_indices"]),
                    "indices": data["token_indices"],
                    "age_seconds": (
                        datetime.now() - datetime.fromisoformat(data["timestamp"])
                    ).total_seconds(),
                }
                for instance, data in allocations.items()
            },
        }

    def _load_allocations(self) -> dict:
        """Load current token allocations"""
        if self.allocation_file.exists():
            try:
                with open(self.allocation_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_allocations(self, allocations: dict):
        """Save token allocations"""
        with open(self.allocation_file, "w") as f:
            json.dump(allocations, f, indent=2)

    def _cleanup_expired(self, allocations: dict) -> dict:
        """Remove expired allocations"""
        cleaned = {}
        now = datetime.now()

        for instance, data in allocations.items():
            timestamp = datetime.fromisoformat(data["timestamp"])
            age = (now - timestamp).total_seconds()

            # Check if allocation is expired or process is dead
            if age < self.token_timeout:
                # Also check if process is still alive
                try:
                    pid = data.get("pid", 0)
                    if pid:
                        os.kill(pid, 0)  # Check if process exists
                    cleaned[instance] = data
                except ProcessLookupError:
                    logger.info(f"Cleaning up dead instance {instance}")
            else:
                logger.info(f"Cleaning up expired instance {instance} (age: {age}s)")

        return cleaned

    def __enter__(self):
        """Context manager entry"""
        self.tokens = self.acquire_tokens()
        return self.tokens

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release tokens"""
        self.release_tokens()


# Convenience function for orchestrators
def get_shared_tokens(max_tokens: int = 5) -> List[str]:
    """
    Get tokens from shared pool

    Args:
        max_tokens: Maximum tokens to request (capped at 5 by default)

    Returns:
        List of allocated tokens
    """
    pool = SharedTokenPool(max_tokens_per_instance=max_tokens)
    return pool.acquire_tokens()


if __name__ == "__main__":
    # Test the shared pool
    pool = SharedTokenPool(max_tokens_per_instance=5)

    print("Current token pool status:")
    status = pool.get_status()
    print(json.dumps(status, indent=2))

    print("\nAcquiring tokens...")
    tokens = pool.acquire_tokens(3)
    print(f"Got {len(tokens)} tokens")

    print("\nUpdated status:")
    status = pool.get_status()
    print(json.dumps(status, indent=2))

    print("\nReleasing tokens...")
    pool.release_tokens()

    print("\nFinal status:")
    status = pool.get_status()
    print(json.dumps(status, indent=2))
