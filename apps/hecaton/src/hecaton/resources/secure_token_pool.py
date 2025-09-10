"""
Secure Token Pool Manager for Claude Code
Manages multiple tokens with rotation for parallel agent execution
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Tuple

from ..utils.enhanced_logging import get_logger, log_resource_usage

logger = get_logger(__name__)

logger = logging.getLogger(__name__)


class SecureTokenPool:
    """Thread-safe token pool with secure storage and rotation"""

    def __init__(self, tokens: Optional[List[str]] = None):
        """Initialize token pool with optional tokens"""
        self._tokens: List[str] = []
        self._token_index = 0
        self._lock = Lock()
        self._usage_stats: Dict[str, Dict] = {}
        self._token_hashes: Dict[str, str] = {}  # Map hash to token for logging

        # Load tokens from various sources
        if tokens:
            self._add_tokens(tokens)
        else:
            self._load_from_environment()

    def _add_tokens(self, tokens: List[str]):
        """Add tokens to pool with security checks"""
        for token in tokens:
            if token and len(token) > 20:  # Basic validation
                self._tokens.append(token)
                # Store hash for safe logging
                token_hash = self._hash_token(token)
                self._token_hashes[token_hash] = f"token_{len(self._tokens)}"
                self._usage_stats[token_hash] = {
                    "added_at": datetime.now().isoformat(),
                    "usage_count": 0,
                    "last_used": None,
                }
                logger.info(
                    f"Added token {self._token_hashes[token_hash]} (hash: {token_hash[:8]}...)"
                )

    def _hash_token(self, token: str) -> str:
        """Create secure hash of token for logging"""
        return hashlib.sha256(token.encode()).hexdigest()

    def _load_from_environment(self):
        """Load tokens from environment variables or config file"""
        # Try loading from config file first
        config_path = Path(
            "/home/opsvi/master_root/apps/hecaton/config/claude_tokens.json"
        )
        if config_path.exists():
            with open(config_path, "r") as f:
                tokens_data = json.load(f)
                # Handle both formats: {"tokens": [...]} or {"CLAUDE_CODE_TOKEN1": "..."}
                if "tokens" in tokens_data and tokens_data["tokens"]:
                    self._add_tokens(tokens_data["tokens"])
                    logger.info(
                        f"Loaded {len(tokens_data['tokens'])} tokens from config file"
                    )
                    return
                # Check for numbered token format
                tokens = []
                for i in range(1, 16):  # Load up to 15 tokens
                    token_key = f"CLAUDE_CODE_TOKEN{i}"
                    if token_key in tokens_data:
                        tokens.append(tokens_data[token_key])
                if tokens:
                    self._add_tokens(tokens)
                    logger.info(f"Loaded {len(tokens)} tokens from config file")
                    return

        # Fall back to environment variables
        primary = os.environ.get("CLAUDE_CODE_TOKEN")
        if primary:
            self._add_tokens([primary])

        # Additional numbered tokens
        for i in range(1, 16):  # Check up to 15 additional tokens
            token_key = f"CLAUDE_CODE_TOKEN{i}"
            token = os.environ.get(token_key)
            if token:
                self._add_tokens([token])

    def add_tokens_from_list(self, tokens: List[str]):
        """Add multiple tokens to the pool"""
        self._add_tokens(tokens)
        logger.info(f"Token pool now has {len(self._tokens)} tokens")

    def get_token(self) -> Tuple[str, str]:
        """Get next available token with round-robin rotation
        Returns: (token, token_id) where token_id is safe for logging
        """
        with self._lock:
            if not self._tokens:
                raise ValueError("No tokens available in pool")

            # Get current token
            token = self._tokens[self._token_index]
            token_hash = self._hash_token(token)
            token_id = self._token_hashes.get(token_hash, "unknown")

            # Update usage stats
            if token_hash in self._usage_stats:
                self._usage_stats[token_hash]["usage_count"] += 1
                self._usage_stats[token_hash]["last_used"] = datetime.now().isoformat()

            # Rotate to next token
            self._token_index = (self._token_index + 1) % len(self._tokens)

            logger.debug(
                f"Allocated {token_id} (usage #{self._usage_stats[token_hash]['usage_count']})"
            )

            return token, token_id

    def acquire(self) -> Tuple[str, str]:
        """Alias for get_token() for compatibility with RealClaudeExecutor"""
        return self.get_token()

    def get_token_count(self) -> int:
        """Get number of tokens in pool"""
        return len(self._tokens)

    def get_usage_stats(self) -> Dict[str, Dict]:
        """Get usage statistics (safe for logging)"""
        with self._lock:
            # Return stats with token IDs instead of hashes
            safe_stats = {}
            for token_hash, stats in self._usage_stats.items():
                token_id = self._token_hashes.get(token_hash, "unknown")
                safe_stats[token_id] = stats.copy()
            return safe_stats

    def save_tokens_encrypted(
        self, filepath: Path, encryption_key: Optional[str] = None
    ):
        """Save tokens to encrypted file (for persistence)"""
        if not encryption_key:
            encryption_key = os.environ.get(
                "CLAUDE_ENCRYPTION_KEY", "default-key-change-me"
            )

        # Simple XOR encryption (replace with proper encryption in production)
        encrypted_tokens = []
        for token in self._tokens:
            encrypted = self._xor_encrypt(token, encryption_key)
            encrypted_tokens.append(encrypted)

        data = {
            "version": "1.0",
            "encrypted": True,
            "tokens": encrypted_tokens,
            "created_at": datetime.now().isoformat(),
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f)

        # Set restrictive permissions
        os.chmod(filepath, 0o600)
        logger.info(f"Saved {len(self._tokens)} encrypted tokens to {filepath}")

    def load_tokens_encrypted(
        self, filepath: Path, encryption_key: Optional[str] = None
    ):
        """Load tokens from encrypted file"""
        if not filepath.exists():
            logger.warning(f"Token file not found: {filepath}")
            return

        if not encryption_key:
            encryption_key = os.environ.get(
                "CLAUDE_ENCRYPTION_KEY", "default-key-change-me"
            )

        with open(filepath) as f:
            data = json.load(f)

        if data.get("encrypted"):
            tokens = []
            for encrypted_token in data.get("tokens", []):
                token = self._xor_decrypt(encrypted_token, encryption_key)
                tokens.append(token)
            self._add_tokens(tokens)
            logger.info(f"Loaded {len(tokens)} tokens from {filepath}")

    def _xor_encrypt(self, text: str, key: str) -> str:
        """Simple XOR encryption (use proper encryption in production)"""
        import base64

        result = []
        for i, char in enumerate(text):
            key_char = key[i % len(key)]
            result.append(chr(ord(char) ^ ord(key_char)))
        return base64.b64encode("".join(result).encode()).decode()

    def _xor_decrypt(self, encrypted: str, key: str) -> str:
        """Simple XOR decryption"""
        import base64

        text = base64.b64decode(encrypted.encode()).decode()
        result = []
        for i, char in enumerate(text):
            key_char = key[i % len(key)]
            result.append(chr(ord(char) ^ ord(key_char)))
        return "".join(result)


class TokenPoolManager:
    """Manages token pool for claude-code servers"""

    _instance: Optional["TokenPoolManager"] = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern for global token pool"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.pool = SecureTokenPool()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "TokenPoolManager":
        """Get singleton instance"""
        return cls()

    def initialize_with_tokens(self, tokens: List[str]):
        """Initialize pool with provided tokens"""
        self.pool.add_tokens_from_list(tokens)

    def get_next_token(self) -> Tuple[str, str]:
        """Get next token for use"""
        return self.pool.get_token()

    def get_pool_status(self) -> Dict:
        """Get pool status for monitoring"""
        return {
            "token_count": self.pool.get_token_count(),
            "usage_stats": self.pool.get_usage_stats(),
        }


# Global instance for easy access
token_pool_manager = TokenPoolManager.get_instance()


def create_safe_environment_with_token(
    base_env: Optional[Dict] = None,
) -> Tuple[Dict[str, str], str]:
    """Create environment with token from pool and ANTHROPIC_API_KEY removed

    Returns:
        (environment_dict, token_id) where token_id is safe for logging
    """
    env = (base_env or os.environ).copy()

    # Remove ANTHROPIC_API_KEY to avoid conflicts
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]

    # Get token from pool
    token, token_id = token_pool_manager.get_next_token()
    env["CLAUDE_CODE_TOKEN"] = token

    return env, token_id


# Initialize default tokens if available
def initialize_default_tokens():
    """Initialize with tokens from environment or config"""
    # Check for tokens file
    token_file = Path.home() / ".claude" / "tokens.enc"
    if token_file.exists():
        token_pool_manager.pool.load_tokens_encrypted(token_file)

    # Add any tokens from environment
    token_pool_manager.pool._load_from_environment()

    logger.info(
        f"Token pool initialized with {token_pool_manager.pool.get_token_count()} tokens"
    )


# Auto-initialize on import
initialize_default_tokens()
