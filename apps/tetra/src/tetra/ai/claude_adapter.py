"""
Claude adapter for Tetra orchestration.
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ClaudeAdapter:
    """Adapter for Claude CLI integration."""

    def __init__(
        self,
        token_pool=None,
        worktree_manager=None,
        claude_bin: str = "claude",
        model: str = "sonnet",
        max_turns: int = 8,
    ):
        """
        Initialize Claude adapter.

        Args:
            token_pool: Token pool for authentication
            worktree_manager: Worktree manager for isolation
            claude_bin: Path to Claude binary
            model: Claude model to use
            max_turns: Maximum conversation turns
        """
        self.token_pool = token_pool
        self.worktree_manager = worktree_manager
        self.claude_bin = claude_bin
        self.model = model
        self.max_turns = max_turns

    def ask(
        self,
        prompt: str,
        system_append: Optional[str] = None,
        mcp_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a prompt using Claude CLI.

        Args:
            prompt: The prompt to execute
            system_append: Additional system instructions
            mcp_config: MCP configuration

        Returns:
            Execution result dictionary
        """
        # Build command
        cmd = [
            self.claude_bin,
            "chat",
            "--model",
            self.model,
            "--max-turns",
            str(self.max_turns),
        ]

        if system_append:
            cmd.extend(["--system-append", system_append])

        # Add MCP config if provided
        if mcp_config:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(mcp_config, f)
                mcp_file = f.name
            cmd.extend(["--mcp", mcp_file])

        try:
            # Execute Claude
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=900,  # 15 minute timeout
            )

            if result.returncode == 0:
                return {
                    "status": "success",
                    "output": result.stdout,
                    "command": " ".join(cmd),
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr,
                    "command": " ".join(cmd),
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Claude execution timed out",
                "command": " ".join(cmd),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "command": " ".join(cmd),
            }
        finally:
            # Cleanup MCP file
            if mcp_config and "mcp_file" in locals():
                Path(mcp_file).unlink(missing_ok=True)
