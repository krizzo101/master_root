"""
Token pool management for parallel Claude execution.
"""

import asyncio
import logging
import os
import random
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class TokenPool:
    """Basic token pool for managing Claude API tokens."""

    def __init__(self, tokens: List[str], max_concurrent: int = 5):
        """
        Initialize token pool.

        Args:
            tokens: List of API tokens
            max_concurrent: Maximum concurrent token usage
        """
        self.tokens = tokens
        self.max_concurrent = max_concurrent
        self.available = list(range(len(tokens)))
        self.lock = threading.Lock()

    def acquire(self, timeout: float = 30.0) -> Tuple[str, int]:
        """
        Acquire a token from the pool.

        Args:
            timeout: Maximum time to wait for a token

        Returns:
            Tuple of (token, token_index)

        Raises:
            TimeoutError: If no token available within timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.lock:
                if self.available:
                    idx = self.available.pop(0)
                    return self.tokens[idx], idx
            time.sleep(0.1)

        raise TimeoutError(f"Could not acquire token within {timeout} seconds")

    def release(self, token_idx: int) -> None:
        """
        Release a token back to the pool.

        Args:
            token_idx: Index of token to release
        """
        with self.lock:
            if token_idx not in self.available:
                self.available.append(token_idx)


class SecureTokenPool:
    """Secure token pool with rotation and encryption support."""

    def __init__(
        self,
        tokens: Optional[List[str]] = None,
        encrypted_file: Optional[Path] = None,
        pool_size: int = 15,
    ):
        """
        Initialize secure token pool.

        Args:
            tokens: Direct token list
            encrypted_file: Path to encrypted token file
            pool_size: Maximum pool size
        """
        self.pool_size = pool_size
        self.tokens = []
        self.current_idx = 0
        self.lock = threading.Lock()

        # Load tokens
        if tokens:
            self.tokens = tokens[:pool_size]
        elif encrypted_file and encrypted_file.exists():
            self._load_encrypted_tokens(encrypted_file)
        else:
            # Try environment variables
            self._load_from_environment()

        if not self.tokens:
            logger.warning("No tokens available in pool")

    def _load_encrypted_tokens(self, file_path: Path) -> None:
        """Load tokens from encrypted file."""
        # Placeholder for encrypted file loading
        logger.info(f"Loading tokens from {file_path}")
        # In production, implement proper decryption here

    def _load_from_environment(self) -> None:
        """Load tokens from environment variables."""
        for i in range(self.pool_size):
            token = os.getenv(f"CLAUDE_TOKEN_{i}")
            if token:
                self.tokens.append(token)

        if not self.tokens:
            # Try single token
            token = os.getenv("ANTHROPIC_API_KEY")
            if token:
                self.tokens = [token]

    def get_token(self) -> Tuple[str, int]:
        """
        Get next token with rotation.

        Returns:
            Tuple of (token, token_id)
        """
        with self.lock:
            if not self.tokens:
                raise ValueError("No tokens available")

            token = self.tokens[self.current_idx]
            token_id = self.current_idx

            # Rotate to next token
            self.current_idx = (self.current_idx + 1) % len(self.tokens)

            return token, token_id

    def add_token(self, token: str) -> None:
        """
        Add a token to the pool.

        Args:
            token: Token to add
        """
        with self.lock:
            if len(self.tokens) < self.pool_size:
                self.tokens.append(token)

    def remove_token(self, token_id: int) -> None:
        """
        Remove a token from the pool.

        Args:
            token_id: ID of token to remove
        """
        with self.lock:
            if 0 <= token_id < len(self.tokens):
                self.tokens.pop(token_id)
                # Adjust current index if needed
                if self.current_idx >= len(self.tokens) and self.tokens:
                    self.current_idx = 0
