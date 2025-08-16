"""CLI commands for the Project Mapper tool.

This module imports and exports all CLI command groups.
"""

from proj_mapper.cli.commands.relationship import relationship_group

__all__ = [
    "relationship_group",
] 