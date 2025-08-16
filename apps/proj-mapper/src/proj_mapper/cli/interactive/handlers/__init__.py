"""Command handlers for interactive shell.

This package contains the handlers for interactive shell commands.
"""

from proj_mapper.cli.interactive.handlers.analyze import handle_analyze
from proj_mapper.cli.interactive.handlers.update import handle_update
from proj_mapper.cli.interactive.handlers.info import handle_info
from proj_mapper.cli.interactive.handlers.config import handle_config
from proj_mapper.cli.interactive.handlers.open import handle_open

__all__ = [
    "handle_analyze",
    "handle_update",
    "handle_info",
    "handle_config",
    "handle_open"
] 