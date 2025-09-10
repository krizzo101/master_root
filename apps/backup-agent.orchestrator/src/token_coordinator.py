#!/usr/bin/env python3
"""
Token Coordinator - Manages token distribution across multiple orchestrator instances
Prevents token contention by assigning dedicated token subsets to each orchestrator
"""

import asyncio
import fcntl
import hashlib
import json
import logging
import os
import socket
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TokenCoordinator:
    """Coordinates token distribution across multiple orchestrator instances"""

    def __init__(
        self, coordination_file: Optional[str] = None, instance_id: Optional[str] = None
    ):
        self.coordination_file = coordination_file or str(
            Path.home() / ".claude" / "orchestrator_coordination.json"
        )
        self.instance_id = instance_id or self._generate_instance_id()
        self.lock_file = f"{self.coordination_file}.lock"

        # Ensure coordination directory exists
        Path(self.coordination_file).parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"TokenCoordinator initialized for instance: {self.instance_id}")

    def _generate_instance_id(self) -> str:
        """Generate unique instance ID based on process and hostname"""
        hostname = socket.gethostname()
        pid = os.getpid()
        timestamp = str(int(time.time()))

        # Create hash for shorter ID
        hash_input = f"{hostname}-{pid}-{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def _load_all_tokens(self) -> List[str]:
        """Load all available tokens from standard sources"""
        from token_loader import TokenLoader

        loader = TokenLoader()
        return loader.load_tokens()

    def _acquire_file_lock(self, file_handle):
        """Acquire exclusive lock on file"""
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except IOError:
            return False

    def _read_coordination_state(self) -> Dict:
        """Read current coordination state with file locking"""
        if not Path(self.coordination_file).exists():
            return {"instances": {}, "token_assignments": {}, "last_update": 0}

        try:
            with open(self.coordination_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"instances": {}, "token_assignments": {}, "last_update": 0}

    def _write_coordination_state(self, state: Dict):
        """Write coordination state with file locking"""
        with open(self.coordination_file, "w") as f:
            if self._acquire_file_lock(f):
                json.dump(state, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            else:
                raise IOError("Could not acquire file lock")

    def register_instance(self, max_parallel: int = 10) -> List[str]:
        """Register this orchestrator instance and get assigned tokens"""

        all_tokens = self._load_all_tokens()

        if not all_tokens:
            logger.error("No tokens available!")
            return []

        logger.info(f"Found {len(all_tokens)} total tokens")

        # Use file locking to coordinate between processes
        lock_path = Path(self.lock_file)

        try:
            with open(lock_path, "w") as lock_f:
                if not self._acquire_file_lock(lock_f):
                    raise RuntimeError(
                        "CATASTROPHIC FAILURE: Could not acquire coordination lock. "
                        "Token coordination is REQUIRED - NO FALLBACKS allowed. "
                        "Fix the coordination system instead of using fallbacks."
                    )

                # Read current state
                state = self._read_coordination_state()

                # Clean up stale instances (older than 5 minutes)
                current_time = time.time()
                active_instances = {}
                for inst_id, info in state["instances"].items():
                    if current_time - info.get("last_seen", 0) < 300:  # 5 minutes
                        active_instances[inst_id] = info

                # Register this instance
                active_instances[self.instance_id] = {
                    "max_parallel": max_parallel,
                    "last_seen": current_time,
                    "pid": os.getpid(),
                    "hostname": socket.gethostname(),
                }

                # Calculate token distribution
                assigned_tokens = self._distribute_tokens(all_tokens, active_instances)

                # Update state
                state.update(
                    {
                        "instances": active_instances,
                        "token_assignments": assigned_tokens,
                        "last_update": current_time,
                    }
                )

                self._write_coordination_state(state)

                my_tokens = assigned_tokens.get(self.instance_id, [])
                logger.info(
                    f"Instance {self.instance_id} assigned {len(my_tokens)} tokens"
                )

                return my_tokens

        except Exception as e:
            raise RuntimeError(
                f"CATASTROPHIC FAILURE: Token coordination error: {e}. "
                "Token coordination is REQUIRED - NO FALLBACKS allowed. "
                "Fix the coordination system instead of using fallbacks."
            )

    def _distribute_tokens(
        self, all_tokens: List[str], instances: Dict
    ) -> Dict[str, List[str]]:
        """Distribute tokens fairly among active instances"""

        if not instances:
            return {}

        # Calculate total demand
        total_demand = sum(info["max_parallel"] for info in instances.values())

        assignments = {}
        token_index = 0

        # Sort instances by ID for deterministic assignment
        sorted_instances = sorted(instances.items())

        for instance_id, info in sorted_instances:
            max_parallel = info["max_parallel"]

            # Calculate fair share based on demand
            share_ratio = max_parallel / total_demand
            token_count = max(1, int(len(all_tokens) * share_ratio))

            # Assign tokens
            instance_tokens = []
            for _ in range(token_count):
                if token_index < len(all_tokens):
                    instance_tokens.append(all_tokens[token_index])
                    token_index += 1

            # If we have leftover tokens, distribute them round-robin
            if token_index < len(all_tokens) and len(instance_tokens) < max_parallel:
                remaining = min(
                    max_parallel - len(instance_tokens), len(all_tokens) - token_index
                )
                instance_tokens.extend(
                    all_tokens[token_index : token_index + remaining]
                )
                token_index += remaining

            assignments[instance_id] = instance_tokens

        return assignments

    def _fallback_token_assignment(
        self, all_tokens: List[str], max_parallel: int
    ) -> List[str]:
        """
        CATASTROPHIC FAILURE: Fallback token assignment is FORBIDDEN

        This method is kept for compatibility but will ALWAYS fail.
        Agents are FORBIDDEN from using fallback mechanisms.
        Token coordination MUST work properly or the system MUST fail.
        """
        raise RuntimeError(
            "CATASTROPHIC FAILURE: Token coordination failed and fallback is FORBIDDEN. "
            "This system requires proper token coordination - NO FALLBACKS allowed. "
            "Fix the coordination system instead of using fallbacks."
        )

    def unregister_instance(self):
        """Unregister this instance from coordination"""
        try:
            with open(self.lock_file, "w") as lock_f:
                if self._acquire_file_lock(lock_f):
                    state = self._read_coordination_state()

                    if self.instance_id in state["instances"]:
                        del state["instances"][self.instance_id]

                    if self.instance_id in state["token_assignments"]:
                        del state["token_assignments"][self.instance_id]

                    state["last_update"] = time.time()
                    self._write_coordination_state(state)

                    logger.info(f"Instance {self.instance_id} unregistered")
        except Exception as e:
            logger.warning(f"Error unregistering instance: {e}")

    def get_coordination_status(self) -> Dict:
        """Get current coordination status"""
        state = self._read_coordination_state()

        return {
            "total_instances": len(state["instances"]),
            "instances": state["instances"],
            "token_assignments": {
                inst_id: len(tokens)
                for inst_id, tokens in state["token_assignments"].items()
            },
            "last_update": state["last_update"],
            "my_instance_id": self.instance_id,
        }


class CoordinatedTokenPool:
    """Token pool that uses coordination for token assignment"""

    def __init__(
        self, max_parallel: int = 10, coordinator: Optional[TokenCoordinator] = None
    ):
        self.coordinator = coordinator or TokenCoordinator()
        self.max_parallel = max_parallel

        # Get assigned tokens
        self.tokens = self.coordinator.register_instance(max_parallel)
        self.available = asyncio.Queue()

        # Initialize queue with assigned tokens
        for i, token in enumerate(self.tokens):
            self.available.put_nowait((token, i))

        logger.info(f"CoordinatedTokenPool initialized with {len(self.tokens)} tokens")

    async def acquire(self) -> Tuple[str, int]:
        """Acquire a token for use"""
        return await self.available.get()

    async def release(self, token: str, token_idx: int):
        """Release a token back to the pool"""
        await self.available.put((token, token_idx))

    def size(self) -> int:
        """Get total token pool size"""
        return len(self.tokens)

    def available_count(self) -> int:
        """Get number of available tokens"""
        return self.available.qsize()

    def get_coordination_status(self) -> Dict:
        """Get coordination status"""
        return self.coordinator.get_coordination_status()

    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.coordinator.unregister_instance()
        except:
            pass


# Convenience functions
def create_coordinated_token_pool(max_parallel: int = 10) -> CoordinatedTokenPool:
    """Create a coordinated token pool"""
    return CoordinatedTokenPool(max_parallel)


def get_coordination_status() -> Dict:
    """Get current coordination status"""
    coordinator = TokenCoordinator()
    return coordinator.get_coordination_status()
