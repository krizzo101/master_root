"""
Secure initialization utilities for Tetra.
"""

import logging
import os
from typing import Any, Dict, Optional

from ..core.orchestrator import Orchestrator
from ..core.token_pool import SecureTokenPool

logger = logging.getLogger(__name__)


def create_secure_orchestrator(config: Optional[Dict[str, Any]] = None) -> Orchestrator:
    """
    Create a secure orchestrator instance.

    Args:
        config: Optional configuration

    Returns:
        Configured Orchestrator instance
    """
    return Orchestrator(config)


def inject_tokens_from_environment(token_pool: SecureTokenPool) -> int:
    """
    Inject tokens from environment variables.

    Args:
        token_pool: Token pool to inject into

    Returns:
        Number of tokens injected
    """
    count = 0

    # Try numbered tokens
    for i in range(20):
        token = os.getenv(f"CLAUDE_TOKEN_{i}")
        if token:
            token_pool.add_token(token)
            count += 1

    # Try single token
    if count == 0:
        token = os.getenv("ANTHROPIC_API_KEY")
        if token:
            token_pool.add_token(token)
            count += 1

    logger.info(f"Injected {count} tokens from environment")
    return count


def get_token_pool_status(token_pool: SecureTokenPool) -> Dict[str, Any]:
    """
    Get status of token pool.

    Args:
        token_pool: Token pool to check

    Returns:
        Status dictionary
    """
    return {
        "total_tokens": len(token_pool.tokens),
        "pool_size": token_pool.pool_size,
        "current_index": token_pool.current_idx,
    }
