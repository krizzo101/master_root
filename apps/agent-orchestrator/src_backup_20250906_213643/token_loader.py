#!/usr/bin/env python3
"""
Token Loader for Agent Orchestrator
Simple token management without external dependencies
"""

import json
import os
from pathlib import Path
from typing import List, Optional


class TokenLoader:
    """Simple token loader that reads from environment or file"""

    def __init__(
        self, tokens_file: Optional[str] = None, orchestrator_type: Optional[str] = None
    ):
        self.orchestrator_type = orchestrator_type

        # Use specific token file based on orchestrator type
        if orchestrator_type == "chat_import":
            self.tokens_file = str(Path.home() / ".claude" / "tokens_chat_import.json")
        elif orchestrator_type == "dashboard":
            self.tokens_file = str(Path.home() / ".claude" / "tokens_dashboard.json")
        elif orchestrator_type == "phase2":
            self.tokens_file = str(Path.home() / ".claude" / "tokens_phase2.json")
        else:
            self.tokens_file = tokens_file or os.environ.get("TOKENS_FILE")

    def load_tokens(self) -> List[str]:
        """Load tokens from various sources"""
        tokens = []

        # If orchestrator type is specified, ONLY use the dedicated token file
        if (
            self.orchestrator_type
            and self.tokens_file
            and Path(self.tokens_file).exists()
        ):
            try:
                with open(self.tokens_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        tokens.extend(data)
                    elif isinstance(data, dict):
                        # Support {"tokens": [...]} format
                        tokens.extend(data.get("tokens", []))

                # Filter out empty strings
                tokens = list(filter(None, tokens))
                return tokens
            except (json.JSONDecodeError, IOError):
                pass

        # Fallback to original behavior for untyped orchestrators
        # 1. Try primary environment variable (Claude Code format ONLY)
        env_token = os.environ.get("CLAUDE_CODE_TOKEN")
        if env_token:
            tokens.append(env_token)

        # 2. Try multiple Claude Code tokens
        env_tokens = os.environ.get("CLAUDE_CODE_TOKENS")
        if env_tokens:
            tokens.extend(env_tokens.split(","))

        # 3. Try tokens file
        if self.tokens_file and Path(self.tokens_file).exists():
            try:
                with open(self.tokens_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        tokens.extend(data)
                    elif isinstance(data, dict):
                        # Support {"tokens": [...]} format
                        tokens.extend(data.get("tokens", []))
            except (json.JSONDecodeError, IOError):
                pass

        # 4. Try default tokens file
        default_file = Path.home() / ".claude" / "tokens.json"
        if default_file.exists():
            try:
                with open(default_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        tokens.extend(data)
                    elif isinstance(data, dict):
                        tokens.extend(data.get("tokens", []))
            except (json.JSONDecodeError, IOError):
                pass

        # Filter out empty strings but allow duplicates for parallel execution
        tokens = list(filter(None, tokens))
        # NOTE: Allow same token multiple times for parallel orchestration

        return tokens

    @staticmethod
    def save_tokens(tokens: List[str], tokens_file: Optional[str] = None):
        """Save tokens to a file"""
        file_path = tokens_file or str(Path.home() / ".claude" / "tokens.json")

        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # Save tokens
        with open(file_path, "w") as f:
            json.dump({"tokens": tokens}, f, indent=2)

        return file_path


# Convenience function
def load_tokens(tokens_file: Optional[str] = None) -> List[str]:
    """Load tokens from all available sources"""
    loader = TokenLoader(tokens_file)
    return loader.load_tokens()
