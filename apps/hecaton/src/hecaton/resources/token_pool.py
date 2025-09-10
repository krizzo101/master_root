"""
Token Pool Manager for HECATON
Phase 0: Manages 2 tokens with thread-safe round-robin rotation
Based on: multi-agent-reference/multi-agent-monitor/orchestration/token_pool.py
"""

import logging
import os
import threading
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class TokenPool:
    """Thread-safe token pool with round-robin rotation for Phase 0 (2 tokens)"""

    def __init__(self):
        """Initialize token pool with 2 tokens from environment"""
        self._tokens: List[str] = []
        self._token_index = 0
        self._lock = threading.Lock()  # Thread safety (CRITICAL: Rule from reference)
        self._usage_count: Dict[int, int] = {}

        # Load tokens from environment
        self._load_tokens()

    def _load_tokens(self):
        """Load exactly 2 tokens for Phase 0"""
        # Token 0: Main token
        token0 = os.environ.get("CLAUDE_CODE_TOKEN")
        if not token0:
            token0 = os.environ.get("CLAUDE_CODE_TOKEN_0")

        # Token 1: Second token
        token1 = os.environ.get("CLAUDE_CODE_TOKEN_1")

        # For Phase 0 testing, we can use the same token twice if needed
        if token0:
            self._tokens.append(token0)
            self._usage_count[0] = 0

            if token1:
                self._tokens.append(token1)
            else:
                # Use same token twice for testing
                logger.warning("CLAUDE_CODE_TOKEN_1 not found, using main token twice")
                self._tokens.append(token0)
            self._usage_count[1] = 0

        # Phase 1 Expansion: Tokens 2-4
        # Added by Agent-1 during self-amplification
        token2 = os.environ.get("CLAUDE_CODE_TOKEN_2")
        if token2:
            self._tokens.append(token2)
            self._usage_count[2] = 0
            logger.info("Loaded token 2 (Phase 1)")

        token3 = os.environ.get("CLAUDE_CODE_TOKEN_3")
        if token3:
            self._tokens.append(token3)
            self._usage_count[3] = 0
            logger.info("Loaded token 3 (Phase 1)")

        token4 = os.environ.get("CLAUDE_CODE_TOKEN_4")
        if token4:
            self._tokens.append(token4)
            self._usage_count[4] = 0
            logger.info("Loaded token 4 (Phase 1)")
        else:
            raise ValueError(
                "No CLAUDE_CODE_TOKEN found in environment. "
                "Please set CLAUDE_CODE_TOKEN and optionally CLAUDE_CODE_TOKEN_1"
            )

        logger.info(f"Token pool initialized with {len(self._tokens)} tokens")

    def acquire(self) -> Tuple[str, int]:
        """
        Acquire next token with round-robin rotation.
        Returns: (token, token_index)
        """
        with self._lock:  # CRITICAL: Thread safety
            if not self._tokens:
                raise ValueError("No tokens available in pool")

            # Get current token
            token = self._tokens[self._token_index]
            current_index = self._token_index

            # Update usage count
            self._usage_count[current_index] += 1

            # Rotate to next token (round-robin)
            self._token_index = (self._token_index + 1) % len(self._tokens)

            logger.debug(
                f"Allocated token {current_index} " f"(usage #{self._usage_count[current_index]})"
            )

            return token, current_index

    def get_token(self) -> str:
        """Simple interface that returns just the token"""
        token, _ = self.acquire()
        return token

    def release(self, token_index: int):
        """
        Release token (placeholder for future enhancement).
        Phase 0: No-op since we use simple round-robin.
        """
        pass

    def get_token_count(self) -> int:
        """Get number of tokens in pool"""
        return len(self._tokens)

    def get_usage_stats(self) -> Dict[str, any]:
        """Get usage statistics"""
        with self._lock:
            return {
                "token_count": len(self._tokens),
                "usage_counts": self._usage_count.copy(),
                "current_index": self._token_index,
            }


# Phase 1+ Extension Point
class ExpandableTokenPool(TokenPool):
    """
    Extended token pool for Phase 1+ that supports dynamic expansion.
    This class will be modified by agents in Phase 1 to support 5 tokens.
    """

    def expand_to_five_tokens(self):
        """
        Phase 1: Expanded to support 5 tokens.
        Modified by Agent-1 during self-amplification.
        """
        # Load additional tokens
        for i in range(2, 5):
            token_key = f"CLAUDE_CODE_TOKEN_{i}"
            token = os.environ.get(token_key)
            if token:
                self._tokens.append(token)
                self._usage_count[i] = 0
                logger.info(f"Expanded: Loaded token {i}")

        logger.info(f"Token pool expanded to {len(self._tokens)} tokens")
