"""Relationship CLI commands.

This package contains CLI commands for relationship detection, analysis, and visualization.
"""

import click

from proj_mapper.cli.commands.relationship.discovery import detect_relationships
from proj_mapper.cli.commands.relationship.analysis import query_relationships
from proj_mapper.cli.commands.relationship.output import export_graph

# Create a command group for relationship commands
@click.group(name="relationship")
def relationship_group():
    """Commands for managing relationships between code and documentation."""
    pass


# Add commands to the group
relationship_group.add_command(detect_relationships)
relationship_group.add_command(query_relationships)
relationship_group.add_command(export_graph)

# Export the command group
__all__ = ["relationship_group"] 