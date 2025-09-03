#!/usr/bin/env python3
"""
Dynamic Token Pool Manager
Intelligently allocates tokens based on demand:
- Single agent gets all tokens
- Multiple agents share fairly (50/50, 33/33/33, etc.)
- Tokens rebalance as tasks complete
"""

import fcntl
import json
import logging
import os
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DynamicTokenPool:
    """
    Manages dynamic token allocation across multiple orchestrator instances

    Key behaviors:
    - Single agent gets all available tokens
    - New agents wait for tokens to become free
    - Tokens redistribute to achieve fair share
    - Released tokens go to waiting agents first
    """

    def __init__(
        self,
        lock_dir: Path = Path("/tmp/token_locks"),
        token_timeout: int = 600,  # 10 minutes for dead process cleanup
        rebalance_interval: int = 5,
    ):  # Check for rebalancing every 5 seconds
        """
        Args:
            lock_dir: Directory for coordination files
            token_timeout: Seconds before considering a process dead
            rebalance_interval: How often to check for rebalancing
        """
        self.lock_dir = lock_dir
        self.lock_dir.mkdir(parents=True, exist_ok=True)

        self.token_timeout = token_timeout
        self.rebalance_interval = rebalance_interval

        # Coordination files
        self.pool_lock_file = self.lock_dir / "dynamic_pool.lock"
        self.state_file = self.lock_dir / "pool_state.json"
        self.request_queue_file = self.lock_dir / "token_requests.json"

        # Instance identity
        self.instance_id = f"pid_{os.getpid()}_{int(time.time())}"

        # Local state
        self.my_tokens = []
        self.total_tokens = []

        # Load all available tokens
        self._load_all_tokens()

        # Start rebalancer thread
        self.running = True
        self.rebalancer = threading.Thread(target=self._rebalancer_loop, daemon=True)
        self.rebalancer.start()

    def _load_all_tokens(self):
        """Load all tokens from encrypted storage"""
        try:
            import sys

            sys.path.insert(0, "/home/opsvi/master_root/apps/multi-agent-monitor")
            from src.orchestration.secrets_manager import TokenSecretsManager

            manager = TokenSecretsManager()
            tokens = manager.load_tokens()

            # Get all token values with their IDs
            self.total_tokens = []
            for key in sorted(tokens.keys()):
                if key.startswith("CLAUDE_CODE_TOKEN"):
                    self.total_tokens.append(
                        {
                            "id": key,
                            "value": tokens[key],
                            "in_use": False,
                            "owner": None,
                            "task_id": None,
                        }
                    )

            logger.info(f"Loaded {len(self.total_tokens)} total tokens")
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            self.total_tokens = []

    def request_tokens(self, count: int = None) -> List[str]:
        """
        Request tokens from the pool

        Args:
            count: Number of tokens requested (None = as many as possible)

        Returns:
            List of token values allocated
        """
        if not self.total_tokens:
            logger.error("No tokens in pool")
            return []

        with self._get_lock():
            state = self._load_state()

            # Clean up dead instances
            state = self._cleanup_dead_instances(state)

            # Register this instance if new
            if self.instance_id not in state["instances"]:
                state["instances"][self.instance_id] = {
                    "pid": os.getpid(),
                    "started": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "tokens": [],
                    "desired_count": count or len(self.total_tokens),
                }
                logger.info(f"New instance {self.instance_id} registered")

            # Update last seen
            state["instances"][self.instance_id][
                "last_seen"
            ] = datetime.now().isoformat()

            # Calculate fair share
            active_instances = len(state["instances"])
            total_available = len(self.total_tokens)
            fair_share = total_available // active_instances

            # If we're the only instance, take all tokens
            if active_instances == 1:
                fair_share = total_available

            # How many tokens do we currently have?
            my_current = len(state["instances"][self.instance_id]["tokens"])

            # How many can we take?
            can_take = fair_share - my_current

            if can_take > 0:
                # Find available tokens
                allocated = []
                for token in state["tokens"]:
                    if not token["in_use"] and len(allocated) < can_take:
                        token["in_use"] = True
                        token["owner"] = self.instance_id
                        allocated.append(token["id"])

                # Update our token list
                state["instances"][self.instance_id]["tokens"].extend(allocated)

                if allocated:
                    logger.info(
                        f"Instance {self.instance_id} acquired {len(allocated)} tokens (total: {len(state['instances'][self.instance_id]['tokens'])})"
                    )

            # Save state
            self._save_state(state)

            # Return actual token values
            my_token_ids = state["instances"][self.instance_id]["tokens"]
            my_tokens = []
            for token in state["tokens"]:
                if token["id"] in my_token_ids:
                    # Find the actual token value
                    for t in self.total_tokens:
                        if t["id"] == token["id"]:
                            my_tokens.append(t["value"])
                            break

            self.my_tokens = my_tokens
            return my_tokens

    def release_token(self, token_index: int):
        """
        Release a specific token back to the pool
        Called when a task using this token completes

        Args:
            token_index: Index of token in self.my_tokens to release
        """
        if token_index >= len(self.my_tokens):
            return

        with self._get_lock():
            state = self._load_state()

            # Find which token ID this is
            released_value = self.my_tokens[token_index]
            released_id = None

            for token in state["tokens"]:
                # Match by value to find ID
                for t in self.total_tokens:
                    if t["value"] == released_value and t["id"] == token["id"]:
                        released_id = token["id"]
                        break
                if released_id:
                    break

            if released_id:
                # Mark token as available
                for token in state["tokens"]:
                    if token["id"] == released_id:
                        token["in_use"] = False
                        token["owner"] = None
                        logger.info(
                            f"Token {released_id} released by {self.instance_id}"
                        )
                        break

                # Remove from our list
                if self.instance_id in state["instances"]:
                    tokens = state["instances"][self.instance_id]["tokens"]
                    if released_id in tokens:
                        tokens.remove(released_id)

                # Check if any other instance is waiting
                self._check_waiting_instances(state)

                self._save_state(state)

    def release_all(self):
        """Release all tokens held by this instance"""
        with self._get_lock():
            state = self._load_state()

            if self.instance_id in state["instances"]:
                my_token_ids = state["instances"][self.instance_id]["tokens"]

                # Mark all our tokens as available
                for token in state["tokens"]:
                    if token["id"] in my_token_ids:
                        token["in_use"] = False
                        token["owner"] = None

                # Clear our token list
                state["instances"][self.instance_id]["tokens"] = []

                logger.info(
                    f"Instance {self.instance_id} released all {len(my_token_ids)} tokens"
                )

                # Check for waiting instances
                self._check_waiting_instances(state)

                # Remove ourselves from instances
                del state["instances"][self.instance_id]

                self._save_state(state)

        self.my_tokens = []

    def _check_waiting_instances(self, state: dict):
        """
        Check if any instances are waiting for tokens and allocate if available
        """
        active_instances = len(state["instances"])
        if active_instances == 0:
            return

        total_available = len(self.total_tokens)
        fair_share = total_available // active_instances

        # Find instances that need more tokens
        for instance_id, instance_data in state["instances"].items():
            current_count = len(instance_data["tokens"])
            if current_count < fair_share:
                # This instance needs more tokens
                need = fair_share - current_count
                allocated = []

                for token in state["tokens"]:
                    if not token["in_use"] and len(allocated) < need:
                        token["in_use"] = True
                        token["owner"] = instance_id
                        allocated.append(token["id"])

                if allocated:
                    instance_data["tokens"].extend(allocated)
                    logger.info(
                        f"Allocated {len(allocated)} tokens to waiting instance {instance_id}"
                    )

    def _rebalancer_loop(self):
        """Background thread that handles rebalancing"""
        while self.running:
            time.sleep(self.rebalance_interval)

            try:
                with self._get_lock():
                    state = self._load_state()
                    state = self._cleanup_dead_instances(state)

                    # Check for rebalancing needs
                    active_instances = len(state["instances"])
                    if active_instances > 1:
                        total_available = len(self.total_tokens)
                        fair_share = total_available // active_instances

                        # Find instances with too many tokens
                        for instance_id, instance_data in state["instances"].items():
                            current_count = len(instance_data["tokens"])
                            if (
                                current_count > fair_share + 1
                            ):  # Allow 1 extra for rounding
                                # This instance should release some tokens
                                excess = current_count - fair_share
                                logger.info(
                                    f"Instance {instance_id} has {excess} excess tokens"
                                )
                                # Note: Actual release happens when tasks complete

                    self._save_state(state)
            except Exception as e:
                logger.error(f"Rebalancer error: {e}")

    def _cleanup_dead_instances(self, state: dict) -> dict:
        """Remove instances that have died or timed out"""
        now = datetime.now()
        dead_instances = []

        for instance_id, instance_data in state["instances"].items():
            # Check if process is alive
            try:
                pid = instance_data.get("pid", 0)
                if pid and pid != os.getpid():  # Don't check ourselves
                    os.kill(pid, 0)

                # Check timeout
                last_seen = datetime.fromisoformat(instance_data["last_seen"])
                if (now - last_seen).total_seconds() > self.token_timeout:
                    dead_instances.append(instance_id)
                    logger.info(f"Instance {instance_id} timed out")

            except ProcessLookupError:
                dead_instances.append(instance_id)
                logger.info(f"Instance {instance_id} process dead")

        # Clean up dead instances
        for instance_id in dead_instances:
            tokens_to_free = state["instances"][instance_id]["tokens"]

            # Free their tokens
            for token in state["tokens"]:
                if token["id"] in tokens_to_free:
                    token["in_use"] = False
                    token["owner"] = None

            del state["instances"][instance_id]
            logger.info(
                f"Cleaned up {len(tokens_to_free)} tokens from dead instance {instance_id}"
            )

        return state

    def _get_lock(self):
        """Get exclusive lock for state modification"""

        class LockContext:
            def __init__(self, lock_file):
                self.lock_file = lock_file
                self.file = None

            def __enter__(self):
                self.file = open(self.lock_file, "w")
                fcntl.flock(self.file, fcntl.LOCK_EX)
                return self

            def __exit__(self, *args):
                fcntl.flock(self.file, fcntl.LOCK_UN)
                self.file.close()

        return LockContext(self.pool_lock_file)

    def _load_state(self) -> dict:
        """Load pool state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except:
                pass

        # Initialize state
        return {
            "tokens": [
                {"id": t["id"], "in_use": False, "owner": None}
                for t in self.total_tokens
            ],
            "instances": {},
        }

    def _save_state(self, state: dict):
        """Save pool state"""
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def get_status(self) -> dict:
        """Get current pool status"""
        with self._get_lock():
            state = self._load_state()
            state = self._cleanup_dead_instances(state)

            total = len(self.total_tokens)
            in_use = sum(1 for t in state["tokens"] if t["in_use"])

            status = {
                "total_tokens": total,
                "in_use": in_use,
                "available": total - in_use,
                "instances": len(state["instances"]),
                "my_tokens": len(self.my_tokens),
                "distribution": {},
            }

            for instance_id, instance_data in state["instances"].items():
                status["distribution"][instance_id] = {
                    "tokens": len(instance_data["tokens"]),
                    "percentage": (len(instance_data["tokens"]) / total * 100)
                    if total > 0
                    else 0,
                    "pid": instance_data.get("pid"),
                }

            return status

    def __del__(self):
        """Cleanup on deletion"""
        self.running = False
        self.release_all()


# Simple interface for orchestrators
def get_dynamic_tokens() -> List[str]:
    """
    Get tokens from dynamic pool
    Will get all available tokens if you're the only one
    Will share fairly if others are running
    """
    pool = DynamicTokenPool()
    return pool.request_tokens()


if __name__ == "__main__":
    # Test/monitor the pool
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "status":
        pool = DynamicTokenPool()
        status = pool.get_status()
        print("Dynamic Token Pool Status:")
        print(f"  Total tokens: {status['total_tokens']}")
        print(f"  In use: {status['in_use']}")
        print(f"  Available: {status['available']}")
        print(f"  Active instances: {status['instances']}")
        print("\nDistribution:")
        for instance, info in status["distribution"].items():
            print(
                f"  {instance}: {info['tokens']} tokens ({info['percentage']:.1f}%) - PID {info['pid']}"
            )
    else:
        # Test allocation
        pool = DynamicTokenPool()
        tokens = pool.request_tokens()
        print(f"Got {len(tokens)} tokens")

        status = pool.get_status()
        print(f"Pool status: {status}")

        print("\nPress Ctrl+C to release tokens...")
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            pass
        finally:
            pool.release_all()
            print("Tokens released")
