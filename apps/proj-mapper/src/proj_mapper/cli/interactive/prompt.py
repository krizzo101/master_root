"""Prompt handling and UI elements for interactive shell.

This module provides UI elements and prompt handling for the interactive shell.
"""

from typing import Dict, Any
from rich.table import Table
from rich.prompt import Prompt, Confirm


def create_help_table() -> Table:
    """Create a table with available commands.
    
    Returns:
        Table: Rich table with commands and descriptions
    """
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description")
    
    # Add rows for each command
    commands = [
        ("analyze <project_path>", "Analyze a project"),
        ("update <project_path>", "Update maps for an existing project"),
        ("info <project_path>", "Get information about a project"),
        ("config [key] [value]", "View or modify configuration"),
        ("open <project_path>", "Set current project"),
        ("help", "Show this help message"),
        ("exit/quit", "Exit the interactive shell"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
        
    return table


def create_project_info_table(project_map: Dict[str, Any]) -> Table:
    """Create a table with project information.
    
    Args:
        project_map: Project map data
        
    Returns:
        Table: Rich table with project information
    """
    table = Table(title="Project Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value")
    
    table.add_row("Project Name", project_map.get("project_name", "Unknown"))
    table.add_row("Schema Version", project_map.get("schema_version", "Unknown"))
    table.add_row("Timestamp", project_map.get("timestamp", "Unknown"))
    
    # Statistics
    files_count = len(project_map.get("files", []))
    modules_count = len(project_map.get("modules", []))
    relationships_count = len(project_map.get("relationships", []))
    
    table.add_row("Files Count", str(files_count))
    table.add_row("Modules Count", str(modules_count))
    table.add_row("Relationships Count", str(relationships_count))
    
    return table


def create_config_table(config: Dict[str, Any]) -> Table:
    """Create a table with configuration values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Table: Rich table with configuration values
    """
    table = Table(title="Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    
    def add_config_rows(config, prefix=""):
        for k, v in config.items():
            if isinstance(v, dict):
                add_config_rows(v, f"{prefix}{k}.")
            else:
                table.add_row(f"{prefix}{k}", str(v))
                
    add_config_rows(config)
    return table


def prompt_for_confirmation(message: str, default: bool = True) -> bool:
    """Prompt for confirmation.
    
    Args:
        message: Message to display
        default: Default value
        
    Returns:
        bool: True if confirmed, False otherwise
    """
    return Confirm.ask(message, default=default)


def prompt_for_input(message: str, default: str = None) -> str:
    """Prompt for input.
    
    Args:
        message: Message to display
        default: Default value
        
    Returns:
        str: User input
    """
    return Prompt.ask(message, default=default) 