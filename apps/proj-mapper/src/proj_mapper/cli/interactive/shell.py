"""Interactive shell implementation for Project Mapper.

This module contains the main InteractiveShell class and interactive mode runner.
"""

import os
import sys
import cmd
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel

from proj_mapper.cli.config_handler import ConfigManager
from proj_mapper.cli.progress import ProgressReporter
from proj_mapper.version import __version__
from proj_mapper.cli.interactive.commands import (
    handle_analyze,
    handle_update,
    handle_info,
    handle_config,
    handle_open
)

# Configure logging
logger = logging.getLogger(__name__)
console = Console()


class InteractiveShell(cmd.Cmd):
    """Interactive command shell for Project Mapper."""
    
    intro = f"""
    Project Mapper Interactive Shell v{__version__}
    Type 'help' or '?' to list commands.
    Type 'exit' or 'quit' to exit.
    """
    prompt = "proj_mapper> "
    
    def __init__(self):
        """Initialize the interactive shell."""
        super().__init__()
        self.console = Console()
        self.config_manager = ConfigManager()
        self.config = self.config_manager._get_default_config()
        self.progress = ProgressReporter(console=self.console)
        self.current_project = None
        
    def do_exit(self, arg):
        """Exit the interactive shell."""
        self.console.print("Goodbye!")
        return True
        
    def do_quit(self, arg):
        """Exit the interactive shell."""
        return self.do_exit(arg)
        
    def do_version(self, arg):
        """Display version information."""
        self.console.print(f"Project Mapper v{__version__}")
        
    def do_help(self, arg):
        """Show help for commands."""
        if arg:
            # Show help for specific command
            super().do_help(arg)
        else:
            # Show general help
            from proj_mapper.cli.interactive.prompt import create_help_table
            table = create_help_table()
            self.console.print(table)
    
    def do_analyze(self, arg):
        """Analyze a project and generate maps."""
        handle_analyze(self, arg)
            
    def do_update(self, arg):
        """Update project maps."""
        handle_update(self, arg)
            
    def do_info(self, arg):
        """Get information about a project."""
        handle_info(self, arg)
            
    def do_config(self, arg):
        """View or modify configuration."""
        handle_config(self, arg)
            
    def do_open(self, arg):
        """Set current project."""
        handle_open(self, arg)


def run_interactive_mode():
    """Run the interactive shell."""
    shell = InteractiveShell()
    
    # Print banner
    console.print(Panel.fit(
        f"[bold cyan]Project Mapper v{__version__}[/bold cyan]\n"
        "[italic]Interactive Mode[/italic]\n"
        "Type 'help' to see available commands",
        title="Project Mapper",
        subtitle="Interactive Shell"
    ))
    
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        console.print("\nExiting interactive mode. Goodbye!")
    
    return 0


if __name__ == "__main__":
    sys.exit(run_interactive_mode()) 