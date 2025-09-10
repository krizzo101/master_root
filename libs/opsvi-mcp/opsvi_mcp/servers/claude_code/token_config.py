"""
Token Configuration and Management
Securely manages Claude Code tokens for the monitoring system
"""

import os
from pathlib import Path
from typing import List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class TokenConfig:
    """Manages token configuration for Claude Code"""
    
    # Token storage locations (in priority order)
    TOKEN_LOCATIONS = [
        Path.home() / ".claude" / "tokens.json",
        Path.home() / ".config" / "claude" / "tokens.json",
        Path("/etc/claude/tokens.json"),
        Path.cwd() / ".claude_tokens.json"
    ]
    
    @staticmethod
    def load_tokens() -> List[str]:
        """Load tokens from configuration files"""
        tokens = []
        
        # Try each location
        for location in TokenConfig.TOKEN_LOCATIONS:
            if location.exists():
                try:
                    with open(location) as f:
                        data = json.load(f)
                        token_list = data.get("tokens", [])
                        tokens.extend(token_list)
                        logger.info(f"Loaded {len(token_list)} tokens from {location}")
                except Exception as e:
                    logger.warning(f"Failed to load tokens from {location}: {e}")
        
        return tokens
    
    @staticmethod
    def save_tokens(tokens: List[str], location: Optional[Path] = None):
        """Save tokens to configuration file"""
        if location is None:
            location = TokenConfig.TOKEN_LOCATIONS[0]
        
        # Create directory if needed
        location.parent.mkdir(parents=True, exist_ok=True)
        
        # Never save raw tokens - save indicators only
        data = {
            "version": "1.0",
            "tokens": ["***REDACTED***" for _ in tokens],
            "count": len(tokens),
            "note": "Actual tokens stored securely in token pool"
        }
        
        with open(location, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(location, 0o600)
        logger.info(f"Saved token configuration to {location}")
    
    @staticmethod
    def add_tokens_to_pool(tokens: List[str]):
        """Add tokens to the global token pool"""
        from .token_pool import token_pool_manager
        
        # Validate tokens
        valid_tokens = []
        for token in tokens:
            if token and len(token) > 20 and token.start